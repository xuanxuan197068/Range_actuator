from __future__ import annotations

import threading
import time
import uuid
from collections.abc import Iterable
from typing import Any

from backend.topo_automation.schemas import OperationJobRecord, ProjectInfo
from backend.topo_automation.session import SessionManager
from backend.topo_automation.settings import AppSettings
from backend.topo_automation.storage import OperationJobStore, OperationLockError
from backend.topo_automation.topo_adapter import TopoApiAdapter


REMOTE_RUNNING = {"deploying", "running", "pending", "created", "queued", "processing", "in_progress"}
REMOTE_SUCCESS = {"success", "succeeded", "completed", "complete", "finished", "deployed"}
REMOTE_FAILURE = {"failed", "fail", "error", "timeout"}
REMOTE_CANCELLED = {"cancelled", "canceled", "cancel", "canceling", "cancelling"}


class DeploymentService:
    def __init__(
        self,
        settings: AppSettings,
        session_manager: SessionManager,
        adapter: TopoApiAdapter,
        operation_store: OperationJobStore,
    ) -> None:
        self._settings = settings
        self._session_manager = session_manager
        self._adapter = adapter
        self._operation_store = operation_store

    def check(self, project_id: str) -> dict[str, Any]:
        cookie = self._session_manager.require_cookie()
        payload = self._adapter.deploy_check(cookie, project_id)
        return {"projectId": project_id, "ok": True, "rawRemotePayload": payload}

    def start_deploy(self, project_id: str) -> OperationJobRecord:
        cookie = self._session_manager.require_cookie()
        project = self._resolve_project(cookie, project_id)
        job_id = uuid.uuid4().hex
        job = self._operation_store.create_job(
            job_id=job_id,
            kind="deploy",
            status="queued",
            project_id=project_id,
            project_name=project.name if project else None,
            progress={"message": "Deploy job queued.", "percent": 0},
        )
        threading.Thread(target=self._run_deploy_job, args=(job.id, project_id), daemon=True).start()
        return job

    def start_cancel(self, project_id: str) -> OperationJobRecord:
        cookie = self._session_manager.require_cookie()
        active = self._operation_store.find_active(project_id)
        if active is not None and active.kind not in {"deploy", "reset"}:
            raise OperationLockError(f"Project {project_id} is locked by active operation {active.id} ({active.kind}:{active.status}).")
        project = self._resolve_project(cookie, project_id)
        remote_deploy_id = active.remoteDeployId if active else self._resolve_running_remote_deploy_id(cookie, project_id)
        job_id = uuid.uuid4().hex
        job = self._operation_store.create_job(
            job_id=job_id,
            kind="cancel",
            status="canceling",
            project_id=project_id,
            project_name=project.name if project else None,
            remote_deploy_id=remote_deploy_id,
            progress={"message": "Cancel job queued.", "percent": 0},
            allow_active=True,
        )
        threading.Thread(target=self._run_cancel_job, args=(job.id, project_id, active.id if active else None), daemon=True).start()
        return job

    def start_reset(self, project_id: str) -> OperationJobRecord:
        cookie = self._session_manager.require_cookie()
        self._operation_store.require_project_idle(project_id)
        project = self._resolve_project(cookie, project_id)
        job_id = uuid.uuid4().hex
        job = self._operation_store.create_job(
            job_id=job_id,
            kind="reset",
            status="queued",
            project_id=project_id,
            project_name=project.name if project else None,
            progress={"message": "Reset job queued.", "percent": 0},
        )
        threading.Thread(target=self._run_reset_job, args=(job.id, project_id), daemon=True).start()
        return job

    def get_job(self, job_id: str) -> OperationJobRecord:
        return self._operation_store.get_job(job_id)

    def get_status(self, project_id: str) -> dict[str, Any]:
        cookie = self._session_manager.require_cookie()
        active = self._operation_store.find_active(project_id)
        latest_jobs = self._operation_store.list_jobs(project_id, limit=5)
        remote_progress = self._safe_fetch_progress(cookie, project_id, active.remoteDeployId if active else None)
        return {
            "projectId": project_id,
            "activeJob": active.model_dump(mode="json") if active else None,
            "recentJobs": [job.model_dump(mode="json") for job in latest_jobs],
            "remoteProgress": remote_progress,
        }

    def _run_deploy_job(self, job_id: str, project_id: str) -> None:
        try:
            cookie = self._session_manager.require_cookie()
            self._operation_store.update_job(job_id, status="checking", progress={"message": "Running deploy check.", "percent": 5})
            check_payload = self._adapter.deploy_check(cookie, project_id)
            self._operation_store.update_job(job_id, status="deploying", raw_remote_payload={"check": check_payload}, progress={"message": "Starting async deploy.", "percent": 10})
            deploy_payload = self._adapter.deploy_project_async(cookie, project_id)
            remote_deploy_id = self._extract_deploy_id(deploy_payload) or self._resolve_remote_deploy_id(cookie, project_id)
            self._operation_store.update_job(
                job_id,
                status="polling",
                remote_deploy_id=remote_deploy_id,
                raw_remote_payload={"check": check_payload, "deploy": deploy_payload},
                progress={"message": "Deployment started.", "percent": 15},
            )
            self._poll_until_final(job_id, project_id, remote_deploy_id)
        except Exception as exc:  # pragma: no cover - network-facing
            self._operation_store.update_job(job_id, status="failed", error=str(exc), progress={"message": str(exc), "percent": 100})

    def _run_cancel_job(self, job_id: str, project_id: str, active_job_id: str | None) -> None:
        try:
            cookie = self._session_manager.require_cookie()
            job = self._operation_store.get_job(job_id)
            remote_deploy_id = job.remoteDeployId or self._resolve_running_remote_deploy_id(cookie, project_id)
            if not remote_deploy_id:
                raise ValueError("Unable to resolve an active remote deploy id to cancel.")
            self._operation_store.update_job(job_id, remote_deploy_id=remote_deploy_id, progress={"message": "Calling remote cancel API.", "percent": 40})
            payload = self._adapter.cancel_deployment(cookie, remote_deploy_id)
            self._operation_store.update_job(
                job_id,
                status="succeeded",
                raw_remote_payload=payload,
                progress={"message": "Deployment cancel requested.", "percent": 100},
            )
            if active_job_id:
                self._operation_store.update_job(
                    active_job_id,
                    status="cancelled",
                    raw_remote_payload={"cancel": payload},
                    progress={"message": "Cancelled by user request.", "percent": 100},
                )
        except Exception as exc:  # pragma: no cover - network-facing
            self._operation_store.update_job(job_id, status="failed", error=str(exc), progress={"message": str(exc), "percent": 100})

    def _run_reset_job(self, job_id: str, project_id: str) -> None:
        payloads: dict[str, Any] = {}
        try:
            cookie = self._session_manager.require_cookie()
            self._operation_store.update_job(job_id, status="canceling", progress={"message": "Checking remote deployment to cancel.", "percent": 5})
            remote_deploy_id = self._resolve_running_remote_deploy_id(cookie, project_id)
            if remote_deploy_id:
                payloads["cancel"] = self._adapter.cancel_deployment(cookie, remote_deploy_id)
            self._operation_store.update_job(job_id, status="clearing", raw_remote_payload=payloads, progress={"message": "Clearing deployed project resources.", "percent": 25})
            payloads["clear"] = self._adapter.clear_project(cookie, project_id, force=True)
            self._operation_store.update_job(job_id, status="checking", raw_remote_payload=payloads, progress={"message": "Running deploy check.", "percent": 45})
            payloads["check"] = self._adapter.deploy_check(cookie, project_id)
            self._operation_store.update_job(job_id, status="deploying", raw_remote_payload=payloads, progress={"message": "Starting async deploy.", "percent": 60})
            payloads["deploy"] = self._adapter.deploy_project_async(cookie, project_id)
            remote_deploy_id = self._extract_deploy_id(payloads["deploy"]) or self._resolve_remote_deploy_id(cookie, project_id)
            self._operation_store.update_job(
                job_id,
                status="polling",
                remote_deploy_id=remote_deploy_id,
                raw_remote_payload=payloads,
                progress={"message": "Redeployment started.", "percent": 65},
            )
            self._poll_until_final(job_id, project_id, remote_deploy_id, floor_percent=65)
        except Exception as exc:  # pragma: no cover - network-facing
            self._operation_store.update_job(job_id, status="failed", error=str(exc), raw_remote_payload=payloads, progress={"message": str(exc), "percent": 100})

    def _poll_until_final(self, job_id: str, project_id: str, remote_deploy_id: str | None, *, floor_percent: int = 15) -> None:
        cookie = self._session_manager.require_cookie()
        deadline = time.monotonic() + self._settings.deployment_timeout_seconds
        best_status = "running"
        best_progress: dict[str, Any] = {"message": "Waiting for remote deployment progress.", "percent": floor_percent}
        while time.monotonic() < deadline:
            payload = self._safe_fetch_progress(cookie, project_id, remote_deploy_id)
            normalized = self._normalize_progress(payload, floor_percent=floor_percent)
            best_status = normalized["remoteStatus"]
            best_progress = normalized
            if not remote_deploy_id:
                remote_deploy_id = normalized.get("remoteDeployId")
            self._operation_store.update_job(
                job_id,
                status="polling",
                remote_deploy_id=remote_deploy_id,
                raw_remote_payload=payload,
                progress=normalized,
            )
            if best_status in {"succeeded", "failed", "cancelled"}:
                final_status = "succeeded" if best_status == "succeeded" else best_status
                self._operation_store.update_job(job_id, status=final_status, progress={**normalized, "percent": 100})
                return
            time.sleep(self._settings.deployment_poll_interval_seconds)
        self._operation_store.update_job(job_id, status="timeout", progress={**best_progress, "message": "Deployment progress polling timed out.", "percent": 100})

    def _safe_fetch_progress(self, cookie: str, project_id: str, remote_deploy_id: str | None) -> dict[str, Any]:
        payload: dict[str, Any] = {"records": None, "ranges": None, "summary": None, "detail": None}
        try:
            payload["records"] = self._adapter.list_deploy_records(cookie, project_id)
        except Exception as exc:  # pragma: no cover - remote shape varies
            payload["recordsError"] = str(exc)
        deploy_id = remote_deploy_id or self._extract_deploy_id(payload.get("records"))
        try:
            payload["ranges"] = self._adapter.list_deploy_ranges(cookie, project_id, deploy_id)
        except Exception as exc:  # pragma: no cover - remote shape varies
            payload["rangesError"] = str(exc)
        range_id = self._extract_range_id(payload.get("ranges"))
        if deploy_id and range_id:
            try:
                payload["summary"] = self._adapter.get_deploy_summary(cookie, project_id, deploy_id=deploy_id, range_id=range_id)
            except Exception as exc:  # pragma: no cover - remote shape varies
                payload["summaryError"] = str(exc)
            try:
                payload["detail"] = self._adapter.get_deploy_detail(cookie, project_id, deploy_id=deploy_id, range_id=range_id)
            except Exception as exc:  # pragma: no cover - remote shape varies
                payload["detailError"] = str(exc)
        payload["remoteDeployId"] = deploy_id
        payload["rangeId"] = range_id
        return payload

    def _resolve_project(self, cookie: str, project_id: str) -> ProjectInfo | None:
        try:
            for project in self._adapter.list_projects(cookie):
                if project.id == project_id:
                    return project
        except Exception:
            return None
        return None

    def _resolve_remote_deploy_id(self, cookie: str, project_id: str) -> str | None:
        try:
            return self._extract_deploy_id(self._adapter.list_deploy_records(cookie, project_id))
        except Exception:
            return None

    def _resolve_running_remote_deploy_id(self, cookie: str, project_id: str) -> str | None:
        try:
            records = self._adapter.list_deploy_records(cookie, project_id)
        except Exception:
            return None
        for item in self._walk(records):
            if not isinstance(item, dict):
                continue
            deploy_id = self._extract_deploy_id(item)
            if deploy_id and self._derive_remote_status(item) == "running":
                return deploy_id
        return None

    def _normalize_progress(self, payload: dict[str, Any], *, floor_percent: int) -> dict[str, Any]:
        percent = self._extract_percent(payload)
        if percent is None:
            percent = floor_percent
        remote_status = self._derive_remote_status(payload)
        remote_deploy_id = payload.get("remoteDeployId")
        if (
            remote_deploy_id
            and not self._payload_contains_deploy_id(payload.get("records"), str(remote_deploy_id))
            and payload.get("summary") is None
            and payload.get("detail") is None
        ):
            remote_status = "running"
        return {
            "message": self._message_for_remote_status(remote_status),
            "percent": max(floor_percent, min(100, int(percent))),
            "remoteStatus": remote_status,
            "remoteDeployId": remote_deploy_id,
            "rangeId": payload.get("rangeId"),
        }

    @staticmethod
    def _message_for_remote_status(status: str) -> str:
        if status == "succeeded":
            return "Deployment completed."
        if status == "failed":
            return "Deployment failed."
        if status == "cancelled":
            return "Deployment cancelled."
        return "Deployment is still running."

    @classmethod
    def _derive_remote_status(cls, payload: Any) -> str:
        values: list[str] = []
        for item in cls._walk(payload):
            if not isinstance(item, dict):
                continue
            for key in ("status", "state", "statusENName", "statusName", "deployStatus", "result"):
                value = item.get(key)
                if value is not None:
                    values.append(str(value).strip().lower())
        words = {value for value in values if value}
        if any(value in REMOTE_FAILURE or "fail" in value or "error" in value for value in words):
            return "failed"
        if any(value in REMOTE_CANCELLED or "cancel" in value for value in words):
            return "cancelled"
        if any(value in REMOTE_RUNNING or "deploying" in value or "running" in value for value in words):
            return "running"
        if any(value in REMOTE_SUCCESS or "success" in value or "complete" in value for value in words):
            return "succeeded"
        return "running"

    @classmethod
    def _extract_deploy_id(cls, payload: Any) -> str | None:
        for item in cls._walk(payload):
            if not isinstance(item, dict):
                continue
            for key in ("deployId", "deploymentId", "deployRecordId", "recordId", "id"):
                value = item.get(key)
                if value not in (None, ""):
                    return str(value)
        return None

    @classmethod
    def _extract_range_id(cls, payload: Any) -> str | None:
        for item in cls._walk(payload):
            if not isinstance(item, dict):
                continue
            for key in ("rangeId", "id"):
                value = item.get(key)
                if value not in (None, ""):
                    return str(value)
        return None

    @classmethod
    def _extract_percent(cls, payload: Any) -> int | None:
        for item in cls._walk(payload):
            if not isinstance(item, dict):
                continue
            for key in ("percent", "progress", "rate", "percentage"):
                value = item.get(key)
                if isinstance(value, (int, float)):
                    return int(value * 100) if 0 <= value <= 1 else int(value)
                if isinstance(value, str) and value.strip().rstrip("%").replace(".", "", 1).isdigit():
                    numeric = float(value.strip().rstrip("%"))
                    return int(numeric * 100) if 0 <= numeric <= 1 else int(numeric)
        return None

    @classmethod
    def _payload_contains_deploy_id(cls, payload: Any, deploy_id: str) -> bool:
        for item in cls._walk(payload):
            if not isinstance(item, dict):
                continue
            for key in ("deployId", "deploymentId", "deployRecordId", "recordId", "id"):
                if str(item.get(key)) == deploy_id:
                    return True
        return False

    @classmethod
    def _walk(cls, payload: Any) -> Iterable[Any]:
        yield payload
        if isinstance(payload, dict):
            for value in payload.values():
                yield from cls._walk(value)
        elif isinstance(payload, list):
            for value in payload:
                yield from cls._walk(value)
