from __future__ import annotations

import copy
import threading
import time
import uuid
from typing import Any

from tools.base64_encoder import encode_text

from backend.topo_automation.schemas import (
    DeviceInfo,
    ExecutionPreview,
    ExecutionSubmitRequest,
    ProjectInfo,
    StageExecutionPreview,
    TargetSelector,
    WorkflowManifest,
    WorkflowStage,
)
from backend.topo_automation.security import compute_script_hash, scan_risk_keywords, summarize_script
from backend.topo_automation.settings import AppSettings
from backend.topo_automation.storage import JobStore, OperationJobStore
from backend.topo_automation.topo_adapter import TopoApiAdapter
from backend.topo_automation.session import SessionManager


FINAL_SUCCESS = {"success"}
FINAL_FAILURE = {"failed", "fail", "error"}
NON_FINAL = {"running", "pending", "dispatching", "queued", "created"}


class ExecutionService:
    def __init__(
        self,
        settings: AppSettings,
        session_manager: SessionManager,
        adapter: TopoApiAdapter,
        store: JobStore,
        operation_store: OperationJobStore | None = None,
    ) -> None:
        self._settings = settings
        self._session_manager = session_manager
        self._adapter = adapter
        self._store = store
        self._operation_store = operation_store

    def build_preview(self, workflow: WorkflowManifest) -> ExecutionPreview:
        cookie = self._session_manager.require_cookie()
        project = self._resolve_project(cookie, workflow)
        all_devices_by_id: dict[str, DeviceInfo] = {}
        stage_previews: list[StageExecutionPreview] = []
        warnings: list[str] = []
        for stage in workflow.stages:
            script_text = self._script_text(stage)
            risk_keywords = scan_risk_keywords(script_text, self._settings.risk_keywords)
            devices = self._resolve_devices(cookie, project.id, workflow.targets_for_stage(stage))
            self._validate_device_compatibility(stage.script.language, devices)
            stage_warnings = [f"{stage.name}: matched risk keyword: {keyword}" for keyword in risk_keywords]
            warnings.extend(stage_warnings)
            for device in devices:
                all_devices_by_id.setdefault(device.id, device)
            stage_previews.append(
                StageExecutionPreview(
                    stageName=stage.name,
                    mode=stage.mode,
                    continueOnFailure=stage.continueOnFailure,
                    devices=devices,
                    preview={
                        "scriptLanguage": stage.script.language,
                        "scriptHash": compute_script_hash(script_text),
                        "scriptSummary": summarize_script(script_text),
                        "riskKeywords": risk_keywords,
                        "mode": stage.mode,
                        "scriptName": stage.name,
                    },
                    warnings=stage_warnings,
                )
            )
        first_stage = stage_previews[0]
        return ExecutionPreview(
            project=project,
            devices=list(all_devices_by_id.values()),
            stageName=first_stage.stageName,
            preview=first_stage.preview,
            stagePreviews=stage_previews,
            warnings=warnings,
        )

    def submit(self, request: ExecutionSubmitRequest) -> dict[str, Any]:
        preview = self.build_preview(request.workflow)
        if request.previewOnly:
            return {"preview": preview.model_dump(mode="json")}
        self._validate_confirmation(request, preview)
        job_id = uuid.uuid4().hex
        if self._operation_store is not None:
            self._operation_store.create_job(
                job_id=job_id,
                kind="execution",
                status="queued",
                project_id=preview.project.id,
                project_name=preview.project.name,
                progress={"message": "Execution job queued.", "percent": 0},
            )
        self._store.create_job(
            job_id=job_id,
            status="validating",
            project_id=preview.project.id,
            project_name=preview.project.name,
            preview=preview,
            request=request.workflow,
            warnings=preview.warnings,
        )
        thread = threading.Thread(target=self._run_job, args=(job_id, copy.deepcopy(request.workflow), preview), daemon=True)
        thread.start()
        return {"jobId": job_id, "status": "validating", "preview": preview.model_dump(mode="json")}

    def run_sync(self, workflow: WorkflowManifest) -> dict[str, Any]:
        preview = self.build_preview(workflow)
        job_id = uuid.uuid4().hex
        if self._operation_store is not None:
            self._operation_store.create_job(
                job_id=job_id,
                kind="execution",
                status="queued",
                project_id=preview.project.id,
                project_name=preview.project.name,
                progress={"message": "Execution job queued.", "percent": 0},
            )
        self._store.create_job(
            job_id=job_id,
            status="validating",
            project_id=preview.project.id,
            project_name=preview.project.name,
            preview=preview,
            request=workflow,
            warnings=preview.warnings,
        )
        self._run_job(job_id, workflow, preview)
        return self._store.get_job(job_id).model_dump(mode="json")

    def get_job(self, job_id: str) -> dict[str, Any]:
        record = self._store.get_job(job_id)
        payload = record.model_dump(mode="json")
        result = payload.get("result")
        if isinstance(result, dict):
            changed = self._enrich_result_logs(result)
            recalculated_status = self._refresh_result_statuses(result)
            if changed or (recalculated_status and recalculated_status != payload.get("status")):
                record = self._store.update_job(
                    job_id,
                    status=recalculated_status or payload.get("status"),
                    result=result,
                    error=payload.get("error"),
                )
                payload = record.model_dump(mode="json")
        return payload

    def list_jobs(self, project_id: str | None = None, *, limit: int = 10) -> list[dict[str, Any]]:
        return [
            job.model_dump(mode="json")
            for job in self._store.list_jobs(project_id, limit=max(1, min(limit, 50)))
        ]

    def _run_job(self, job_id: str, workflow: WorkflowManifest, preview: ExecutionPreview) -> None:
        cookie = self._session_manager.require_cookie()
        stage_results: list[dict[str, Any]] = []
        all_device_results: list[dict[str, Any]] = []
        try:
            for index, stage in enumerate(workflow.stages):
                stage_preview = preview.stagePreviews[index]
                content_b64 = encode_text(self._script_text(stage))
                metadata = stage.metadata or {}
                script_creations: list[dict[str, Any]] = []
                dispatch_payload: list[dict[str, Any]] = []
                stage_prefix = f"stage {index + 1}/{len(workflow.stages)}: {stage.name}"

                self._update_status(job_id, "creating_scripts", progress_message=f"Creating scripts for {stage_prefix}.", stage_index=index, total_stages=len(workflow.stages))
                failures = self._create_scripts(
                    cookie,
                    project=preview.project,
                    devices=stage_preview.devices,
                    script_name=stage.name,
                    content_b64=content_b64,
                    metadata=metadata,
                    script_creations=script_creations,
                )
                if failures:
                    for failure in failures:
                        failure.setdefault("stageName", stage.name)
                    stage_result = {
                        "stageName": stage.name,
                        "status": "failed",
                        "scriptCreations": script_creations,
                        "deviceResults": failures,
                        "error": "One or more script creations failed.",
                    }
                    stage_results.append(stage_result)
                    all_device_results.extend(failures)
                    if not stage.continueOnFailure:
                        break
                    continue

                self._update_status(job_id, "dispatching", progress_message=f"Dispatching scripts for {stage_prefix}.", stage_index=index, total_stages=len(workflow.stages))
                dispatch_payload = self._adapter.run_private_scripts(
                    cookie,
                    device_ids=[device.id for device in stage_preview.devices],
                    mode=stage.mode,
                )

                partial_result = {"stageResults": stage_results, "dispatch": dispatch_payload, "scriptCreations": script_creations}
                self._store.update_job(job_id, status="polling_logs", result=partial_result)
                self._update_operation(job_id, "polling_logs", progress={"message": f"Polling logs for {stage_prefix}.", "percent": self._stage_percent(index, 70, len(workflow.stages))})
                device_results = self._poll_logs(cookie, preview.project, stage_preview.devices, stage.mode, script_creations)
                for item in device_results:
                    item.setdefault("stageName", stage.name)
                stage_status = self._calculate_final_status(device_results)
                stage_result = {
                    "stageName": stage.name,
                    "mode": stage.mode,
                    "continueOnFailure": stage.continueOnFailure,
                    "status": stage_status,
                    "scriptCreations": script_creations,
                    "dispatch": dispatch_payload,
                    "deviceResults": device_results,
                }
                stage_results.append(stage_result)
                all_device_results.extend(device_results)
                if stage_status != "succeeded" and not stage.continueOnFailure:
                    break

            overall_status = self._calculate_overall_status(stage_results)
            result_payload = {
                "project": preview.project.model_dump(mode="json"),
                "preview": preview.model_dump(mode="json"),
                "stageResults": stage_results,
                "deviceResults": all_device_results,
            }
            self._store.update_job(job_id, status=overall_status, result=result_payload)
            self._update_operation(job_id, overall_status, progress={"message": f"Execution finished with status {overall_status}.", "percent": 100})
        except Exception as exc:  # pragma: no cover - network-facing
            self._store.update_job(job_id, status="failed", error=str(exc), result={"stageResults": stage_results, "deviceResults": all_device_results})
            self._update_operation(job_id, "failed", progress={"message": str(exc), "percent": 100}, error=str(exc))

    def _create_scripts(
        self,
        cookie: str,
        project: ProjectInfo,
        devices: list[DeviceInfo],
        script_name: str,
        content_b64: str,
        metadata: dict[str, Any],
        script_creations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        failures: list[dict[str, Any]] = []
        for device in devices:
            try:
                created = self._adapter.create_private_script(
                    cookie,
                    project_id=project.id,
                    device_id=device.id,
                    script_name=script_name,
                    content_b64=content_b64,
                    metadata=metadata,
                )
                script_creations.append({"deviceId": device.id, "scriptId": created.get("id"), "status": "created"})
            except Exception as exc:  # pragma: no cover - network-facing
                failures.append({"deviceId": device.id, "status": "create_failed", "error": str(exc)})
        return failures

    def _poll_logs(
        self,
        cookie: str,
        project: ProjectInfo,
        devices: list[DeviceInfo],
        mode: str,
        script_creations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        deadline = time.monotonic() + self._settings.execution_timeout_seconds
        by_device = {device.id: {"deviceId": device.id, "scriptId": None, "status": "pending"} for device in devices}
        for item in script_creations:
            by_device[item["deviceId"]]["scriptId"] = item["scriptId"]

        while time.monotonic() < deadline:
            all_final = True
            for device in devices:
                current = by_device[device.id]
                if (current.get("status") or "").lower() in FINAL_SUCCESS | FINAL_FAILURE:
                    continue
                logs = self._adapter.list_script_logs(
                    cookie,
                    project_id=project.id,
                    script_id=current.get("scriptId"),
                    device_id=device.id,
                    mode=mode,
                )
                if not logs:
                    all_final = False
                    continue
                latest = logs[0]
                status = str(latest.get("status") or "pending").lower()
                current["status"] = status
                self._apply_log_to_result(current, latest)
                if status in NON_FINAL:
                    all_final = False
            if all_final:
                break
            time.sleep(self._settings.execution_poll_interval_seconds)

        results: list[dict[str, Any]] = []
        for device in devices:
            result = by_device[device.id]
            status = str(result.get("status") or "pending").lower()
            if status in NON_FINAL or status == "pending":
                result["status"] = "timeout"
            results.append(result)
        return results

    def _enrich_result_logs(self, result: dict[str, Any]) -> bool:
        project = result.get("project") if isinstance(result.get("project"), dict) else {}
        project_id = project.get("id")
        if not project_id:
            return False
        try:
            cookie = self._session_manager.require_cookie()
        except Exception:
            return False

        result_rows: list[dict[str, Any]] = []
        for row in result.get("deviceResults") or []:
            if isinstance(row, dict):
                result_rows.append(row)
        for stage in result.get("stageResults") or []:
            if not isinstance(stage, dict):
                continue
            for row in stage.get("deviceResults") or []:
                if isinstance(row, dict):
                    result_rows.append(row)

        log_cache: dict[tuple[str | None, str | None], dict[str, Any] | None] = {}
        changed = False
        for row in result_rows:
            if not row.get("scriptId"):
                continue
            row_status = str(row.get("status") or "").lower()
            has_message = bool(row.get("errMsg") or row.get("outMsg"))
            if has_message and row_status in FINAL_SUCCESS | FINAL_FAILURE:
                continue
            key = (row.get("deviceId"), row.get("scriptId"))
            if key not in log_cache:
                try:
                    logs = self._adapter.list_script_logs(
                        cookie,
                        project_id=project_id,
                        script_id=row.get("scriptId"),
                        device_id=row.get("deviceId"),
                        mode=None,
                    )
                    log_cache[key] = logs[0] if logs else None
                except Exception:
                    log_cache[key] = None
            if log_cache[key]:
                before = {
                    "status": row.get("status"),
                    "executeId": row.get("executeId"),
                    "outMsg": row.get("outMsg"),
                    "errMsg": row.get("errMsg"),
                    "message": row.get("message"),
                    "logId": row.get("logId"),
                }
                self._apply_log_to_result(row, log_cache[key])
                after = {
                    "status": row.get("status"),
                    "executeId": row.get("executeId"),
                    "outMsg": row.get("outMsg"),
                    "errMsg": row.get("errMsg"),
                    "message": row.get("message"),
                    "logId": row.get("logId"),
                }
                changed = changed or before != after
        return changed

    @staticmethod
    def _apply_log_to_result(result: dict[str, Any], latest: dict[str, Any]) -> None:
        status = str(latest.get("status") or result.get("status") or "pending").lower()
        out_msg = latest.get("outMsg")
        err_msg = latest.get("errMsg")
        raw_log = {key: value for key, value in latest.items() if key != "content"}
        result.update(
            {
                "status": status,
                "executeId": latest.get("executeId"),
                "scriptName": latest.get("scriptName"),
                "outMsg": out_msg,
                "errMsg": err_msg,
                "message": err_msg or out_msg or latest.get("message"),
                "logId": latest.get("id"),
                "rawLog": raw_log,
            }
        )

    def _refresh_result_statuses(self, result: dict[str, Any]) -> str | None:
        stage_results = result.get("stageResults")
        if not isinstance(stage_results, list) or not stage_results:
            return None
        all_device_results: list[dict[str, Any]] = []
        for stage in stage_results:
            if not isinstance(stage, dict):
                continue
            device_results = [row for row in stage.get("deviceResults") or [] if isinstance(row, dict)]
            if device_results:
                stage["status"] = self._calculate_final_status(device_results)
                all_device_results.extend(device_results)
        if all_device_results:
            result["deviceResults"] = all_device_results
        return self._calculate_overall_status([stage for stage in stage_results if isinstance(stage, dict)])

    @staticmethod
    def _calculate_final_status(device_results: list[dict[str, Any]]) -> str:
        statuses = {str(item.get("status") or "pending").lower() for item in device_results}
        if statuses == {"success"}:
            return "succeeded"
        if "timeout" in statuses and statuses <= {"success", "timeout"}:
            return "timeout"
        if statuses & FINAL_SUCCESS and statuses - FINAL_SUCCESS:
            return "partially_succeeded"
        if statuses & FINAL_FAILURE:
            return "failed"
        return "timeout"

    @staticmethod
    def _calculate_overall_status(stage_results: list[dict[str, Any]]) -> str:
        if not stage_results:
            return "failed"
        statuses = {str(item.get("status") or "failed").lower() for item in stage_results}
        if statuses == {"succeeded"}:
            return "succeeded"
        if "failed" in statuses:
            return "failed" if len(statuses) == 1 else "partially_succeeded"
        if "timeout" in statuses:
            return "timeout" if statuses <= {"timeout", "succeeded"} else "partially_succeeded"
        if statuses - {"succeeded"}:
            return "partially_succeeded"
        return "succeeded"

    @staticmethod
    def _script_text(stage: WorkflowStage) -> str:
        if not stage.script.inline:
            raise ValueError(f"Stage {stage.name} must contain inline script content before execution.")
        return stage.script.inline

    def _update_status(self, job_id: str, status: str, *, progress_message: str, stage_index: int, total_stages: int) -> None:
        self._store.update_job(job_id, status=status)
        self._update_operation(
            job_id,
            status,
            progress={"message": progress_message, "percent": self._stage_percent(stage_index, 40, total_stages)},
        )

    def _update_operation(
        self,
        job_id: str,
        status: str,
        *,
        progress: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        if self._operation_store is not None:
            self._operation_store.update_job(job_id, status=status, progress=progress, error=error)

    @staticmethod
    def _stage_percent(stage_index: int, base: int, total_stages: int) -> int:
        total = max(1, total_stages)
        return min(99, int(base + (stage_index / total) * (99 - base)))

    def _resolve_project(self, cookie: str, workflow: WorkflowManifest) -> ProjectInfo:
        projects = self._adapter.list_projects(cookie)
        selector = workflow.project
        if selector.id:
            for project in projects:
                if project.id == selector.id:
                    return project
            raise ValueError(f"Project id not found: {selector.id}")
        matches = [project for project in projects if project.name == selector.name]
        if len(matches) != 1:
            raise ValueError(f"Project name must resolve to exactly one project: {selector.name}")
        return matches[0]

    def _resolve_devices(self, cookie: str, project_id: str, selector: TargetSelector) -> list[DeviceInfo]:
        devices = self._adapter.list_devices(cookie, project_id)
        if selector.deviceIds:
            resolved = [device for device in devices if device.id in set(selector.deviceIds)]
            if len(resolved) != len(selector.deviceIds):
                found_ids = {device.id for device in resolved}
                missing = [device_id for device_id in selector.deviceIds if device_id not in found_ids]
                raise ValueError(f"Unknown device ids: {', '.join(missing)}")
            return resolved

        resolved: list[DeviceInfo] = []
        for name in selector.deviceNames:
            matches = [device for device in devices if device.name == name]
            if len(matches) != 1:
                raise ValueError(f"Device name must resolve to exactly one device within the project: {name}")
            resolved.append(matches[0])
        return resolved

    @staticmethod
    def _validate_device_compatibility(language: str, devices: list[DeviceInfo]) -> None:
        expected_family = "linux" if language == "bash" else "windows"
        actual_families = {device.osFamily for device in devices}
        if "unknown" in actual_families:
            raise ValueError("Some selected devices do not expose a detectable operating system family.")
        if len(actual_families) != 1:
            raise ValueError("Mixed operating system families are not supported in one stage.")
        only_family = next(iter(actual_families))
        if only_family != expected_family:
            raise ValueError(f"Script language {language} is incompatible with device family {only_family}.")

    def _validate_confirmation(self, request: ExecutionSubmitRequest, preview: ExecutionPreview) -> None:
        if not request.confirmRisk:
            raise ValueError("Execution requires explicit risk confirmation.")
