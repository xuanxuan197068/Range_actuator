from __future__ import annotations

import base64
import json
from typing import Any

from backend.topo_automation.schemas import DeviceInfo, ProjectInfo, ScriptDetail, ScriptInfo
from backend.topo_automation.security import compute_script_hash, summarize_script
from backend.topo_automation.settings import AppSettings
from tools.topo_api_client import send_request
from tools.base64_encoder import encode_text


class TopoApiError(RuntimeError):
    """Raised when the remote topo API returns an unexpected response."""


class TopoApiAdapter:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def _call(
        self,
        method: str,
        *,
        cookie: str,
        path: str,
        params: list[str] | None = None,
        json_obj: Any | None = None,
    ) -> Any:
        response = send_request(
            method,
            base_url=self._settings.topo_base_url,
            path=path,
            params=params or [],
            cookie=cookie,
            json_text=json.dumps(json_obj, ensure_ascii=False) if json_obj is not None else None,
            timeout=self._settings.session_timeout_seconds,
        )
        body_text = response.body_text.strip()
        if not body_text:
            if response.status >= 400:
                raise TopoApiError(f"HTTP {response.status} calling {path}")
            return None
        try:
            payload = json.loads(body_text)
        except json.JSONDecodeError as exc:
            if response.status >= 400:
                raise TopoApiError(f"Invalid JSON response from {path}: {exc}") from exc
            return body_text
        if response.status >= 400:
            raise TopoApiError(payload.get("message") or f"HTTP {response.status} calling {path}")
        if payload.get("code") != 1:
            raise TopoApiError(payload.get("message") or f"Unexpected response code from {path}")
        return payload.get("data")

    def validate_cookie(self, cookie: str) -> bool:
        try:
            self._call(
                "get",
                cookie=cookie,
                path="/projects",
                params=["pageIndex=1", "pageSize=1"],
            )
        except TopoApiError:
            return False
        return True

    def list_projects(self, cookie: str) -> list[ProjectInfo]:
        items = self._list_paginated(cookie, "/projects")
        return [self._sanitize_project(item) for item in items]

    def list_devices(self, cookie: str, project_id: str) -> list[DeviceInfo]:
        items = self._list_paginated(cookie, "/device_scripts/devices/deployed", extra_params=[f"projectId={project_id}"])
        return [self._sanitize_device(item) for item in items]

    def list_scripts(
        self,
        cookie: str,
        *,
        project_id: str,
        device_id: str | None = None,
        script_name: str | None = None,
        script_type: str | None = None,
    ) -> list[ScriptInfo]:
        extra_params = [f"projectId={project_id}"]
        if device_id:
            extra_params.append(f"deviceId={device_id}")
        if script_name:
            extra_params.append(f"name={script_name}")
        if script_type:
            extra_params.append(f"type={script_type}")
        items = self._list_paginated(cookie, "/device_scripts", extra_params=extra_params)
        return [self._sanitize_script(item) for item in items]

    def get_script(self, cookie: str, script_id: str) -> ScriptDetail:
        data = self._call("get", cookie=cookie, path=f"/device_scripts/{script_id}")
        if not isinstance(data, dict):
            raise TopoApiError(f"Unexpected script payload for {script_id}")
        return self._sanitize_script(data, include_content=True)

    def update_script(
        self,
        cookie: str,
        *,
        script_id: str,
        project_id: str,
        script_text: str,
        name: str | None,
        metadata: dict[str, Any] | None,
        ready: bool | None,
    ) -> ScriptDetail:
        payload: dict[str, Any] = {
            "projectId": project_id,
            "content": encode_text(script_text),
        }
        if name is not None:
            payload["name"] = name
        serialized_metadata = self._serialize_metadata(metadata)
        if serialized_metadata is not None:
            payload["metadata"] = serialized_metadata
        if ready is not None:
            payload["ready"] = ready
        data = self._call("put", cookie=cookie, path=f"/device_scripts/{script_id}", json_obj=payload)
        if isinstance(data, dict):
            return self._sanitize_script(data, include_content=True)
        return self.get_script(cookie, script_id)

    def mark_script_ready(self, cookie: str, *, script_id: str, device_id: str) -> ScriptDetail:
        self._call("put", cookie=cookie, path=f"/device_scripts/{script_id}/ready", params=[f"deviceId={device_id}"])
        return self.get_script(cookie, script_id)

    def delete_script(self, cookie: str, script_id: str) -> None:
        self._call("delete", cookie=cookie, path=f"/device_scripts/{script_id}")

    def create_private_script(
        self,
        cookie: str,
        *,
        project_id: str,
        device_id: str,
        script_name: str,
        content_b64: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "projectId": project_id,
            "deviceId": device_id,
            "name": script_name,
            "content": content_b64,
            "ready": True,
        }
        serialized_metadata = self._serialize_metadata(metadata)
        if serialized_metadata is not None:
            payload["metadata"] = serialized_metadata
        return self._call("post", cookie=cookie, path="/device_scripts", json_obj=payload)

    def run_private_scripts(self, cookie: str, *, device_ids: list[str], mode: str) -> list[dict[str, Any]]:
        data = self._call(
            "post",
            cookie=cookie,
            path="/device_scripts/run/private",
            params=[f"mode={mode}"],
            json_obj=device_ids,
        )
        return data if isinstance(data, list) else []

    def list_script_logs(
        self,
        cookie: str,
        *,
        project_id: str,
        script_id: str | None = None,
        device_id: str | None = None,
        mode: str | None = None,
    ) -> list[dict[str, Any]]:
        params = [f"projectId={project_id}", "pageIndex=1", "pageSize=10"]
        if script_id:
            params.append(f"scriptId={script_id}")
        if device_id:
            params.append(f"deviceId={device_id}")
        if mode:
            params.append(f"mode={mode}")
        data = self._call("get", cookie=cookie, path="/device_scripts/logs", params=params)
        items = data.get("items") if isinstance(data, dict) else None
        return items if isinstance(items, list) else []

    def deploy_check(self, cookie: str, project_id: str) -> Any:
        return self._call("post", cookie=cookie, path=f"/projects/{project_id}/deploy/check")

    def deploy_project_async(self, cookie: str, project_id: str) -> Any:
        return self._call("post", cookie=cookie, path=f"/projects/{project_id}/deploy/async")

    def cancel_deployment(self, cookie: str, deploy_id: str) -> Any:
        return self._call("post", cookie=cookie, path=f"/projects/deploying/{deploy_id}/cancel")

    def clear_project(self, cookie: str, project_id: str, *, force: bool = True) -> Any:
        return self._call("post", cookie=cookie, path=f"/project/clear/{project_id}", params=[f"force={str(force).lower()}"])

    def list_deploy_records(self, cookie: str, project_id: str) -> Any:
        return self._call(
            "get",
            cookie=cookie,
            path=f"/projects/{project_id}/deploy/records",
            params=["pageIndex=1", "pageSize=10"],
        )

    def list_deploy_ranges(self, cookie: str, project_id: str, deploy_id: str | None = None) -> Any:
        params = [f"deployId={deploy_id}"] if deploy_id else []
        return self._call("get", cookie=cookie, path=f"/projects/{project_id}/ranges", params=params)

    def get_deploy_summary(
        self,
        cookie: str,
        project_id: str,
        *,
        deploy_id: str,
        range_id: str,
    ) -> Any:
        return self._call(
            "get",
            cookie=cookie,
            path=f"/projects/{project_id}/deploy/{deploy_id}/summary",
            params=[f"rangeId={range_id}", "pageIndex=1", f"pageSize={self._settings.api_page_size}"],
        )

    def get_deploy_detail(
        self,
        cookie: str,
        project_id: str,
        *,
        deploy_id: str,
        range_id: str,
    ) -> Any:
        return self._call(
            "get",
            cookie=cookie,
            path=f"/projects/{project_id}/deploy/{deploy_id}/detail",
            params=[f"rangeId={range_id}", "pageIndex=1", f"pageSize={self._settings.api_page_size}"],
        )

    def _list_paginated(self, cookie: str, path: str, *, extra_params: list[str] | None = None) -> list[dict[str, Any]]:
        page_index = 1
        all_items: list[dict[str, Any]] = []
        total = None
        while total is None or len(all_items) < total:
            params = [f"pageIndex={page_index}", f"pageSize={self._settings.api_page_size}"]
            if extra_params:
                params.extend(extra_params)
            data = self._call("get", cookie=cookie, path=path, params=params)
            if not isinstance(data, dict):
                raise TopoApiError(f"Unexpected paginated response shape for {path}")
            items = data.get("items") or []
            if not isinstance(items, list):
                raise TopoApiError(f"Unexpected items payload for {path}")
            total = int(data.get("total") or len(items))
            all_items.extend(items)
            if not items:
                break
            page_index += 1
        return all_items

    @staticmethod
    def _sanitize_project(item: dict[str, Any]) -> ProjectInfo:
        return ProjectInfo(
            id=str(item.get("id")),
            name=str(item.get("name")),
            status=item.get("statusENName") or item.get("statusCHName"),
            vmCount=item.get("vmCount"),
            updated=item.get("updated"),
        )

    @staticmethod
    def _sanitize_device(item: dict[str, Any]) -> DeviceInfo:
        sys_type = (item.get("sysType") or "").lower()
        if "win" in sys_type:
            family = "windows"
        elif sys_type:
            family = "linux"
        else:
            family = "unknown"

        ip_addresses: list[str] = []
        for address in item.get("addresses") or []:
            for ip_item in address.get("ips") or []:
                ip_value = ip_item.get("ipAddress")
                if ip_value:
                    ip_addresses.append(str(ip_value))

        router_script = item.get("routerScript") or {}
        return DeviceInfo(
            id=str(item.get("id")),
            name=str(item.get("name")),
            projectId=str(item.get("projectId")),
            projectName=item.get("projectName"),
            sysType=item.get("sysType"),
            osFamily=family,
            vmType=item.get("vmType"),
            instanceName=item.get("instanceName"),
            networkName=item.get("networkName"),
            ipAddresses=ip_addresses,
            lastScriptName=router_script.get("scriptName"),
            lastScriptStatus=router_script.get("status"),
        )

    @classmethod
    def _sanitize_script(cls, item: dict[str, Any], *, include_content: bool = False) -> ScriptInfo | ScriptDetail:
        script_id = (
            item.get("id")
            or item.get("routerScriptId")
            or item.get("rangeRouterScriptId")
            or item.get("scriptId")
        )
        content_b64 = item.get("content")
        script_text = cls._decode_script_content(content_b64) if include_content else None
        script_hash = compute_script_hash(script_text) if script_text is not None else None
        script_summary = summarize_script(script_text) if script_text is not None else None
        payload: dict[str, Any] = {
            "id": str(script_id),
            "name": item.get("name") or item.get("routerScriptName"),
            "projectId": item.get("projectId"),
            "projectName": item.get("projectName"),
            "deviceId": item.get("deviceId"),
            "deviceName": item.get("deviceName") or item.get("instanceName") or item.get("useName"),
            "type": item.get("type"),
            "ready": item.get("ready"),
            "created": item.get("created") or item.get("createdAt"),
            "updated": item.get("updated") or item.get("updatedAt"),
            "metadata": cls._normalize_metadata(item.get("metadata")),
            "scriptHash": script_hash,
            "scriptSummary": script_summary,
        }
        if include_content:
            payload["contentBase64"] = content_b64
            payload["scriptText"] = script_text
            return ScriptDetail.model_validate(payload)
        return ScriptInfo.model_validate(payload)

    @staticmethod
    def _normalize_metadata(raw_metadata: Any) -> dict[str, str]:
        if isinstance(raw_metadata, dict):
            return {str(key): str(value) for key, value in raw_metadata.items()}
        if isinstance(raw_metadata, list):
            normalized: dict[str, str] = {}
            for item in raw_metadata:
                if not isinstance(item, dict):
                    continue
                key = item.get("key")
                value = item.get("value")
                if key is not None:
                    normalized[str(key)] = "" if value is None else str(value)
            return normalized
        return {}

    @staticmethod
    def _decode_script_content(content_b64: Any) -> str | None:
        if not isinstance(content_b64, str) or not content_b64:
            return None
        try:
            decoded = base64.b64decode(content_b64)
            return decoded.decode("utf-8", errors="replace")
        except Exception:
            return None

    @staticmethod
    def _serialize_metadata(metadata: dict[str, Any] | None) -> dict[str, str] | None:
        if not metadata:
            return None
        return {
            str(key): "" if value is None else str(value)
            for key, value in metadata.items()
        }
