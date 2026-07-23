from __future__ import annotations

import base64
from typing import Any

from .models import DeviceInfo, ProjectInfo, ScriptInfo, ScriptLog
from .security import compute_script_hash, summarize_script, truncate
from .settings import Settings
from .transport import AsyncTransport, TopoApiError


def _str_or_none(value: Any) -> str | None:
    return None if value is None else str(value)


class TopoApiAdapter:
    """异步靶场 API 适配层：只接收相对 path，自动翻页，出口脱敏（永不返回脚本内容/Cookie）。"""

    def __init__(self, transport: AsyncTransport, settings: Settings) -> None:
        self._t = transport
        self._settings = settings

    # ---- 探活 ----

    async def validate_cookie(self) -> bool:
        try:
            await self._t.request("get", "/projects", params={"pageIndex": 1, "pageSize": 1})
        except TopoApiError:
            return False
        return True

    # ---- 查询 ----

    async def list_projects(self) -> tuple[list[ProjectInfo], bool]:
        items, truncated = await self._list_paginated("/projects")
        return [self._sanitize_project(i) for i in items], truncated

    async def list_devices(
        self,
        project_id: str,
        *,
        name: str | None = None,
        ip: str | None = None,
        sys_type: str | None = None,
    ) -> tuple[list[DeviceInfo], bool]:
        extra: dict[str, Any] = {"projectId": project_id}
        if name:
            extra["name"] = name
        if ip:
            extra["ipAddress"] = ip
        if sys_type:
            extra["sysType"] = sys_type
        items, truncated = await self._list_paginated(
            "/device_scripts/devices/deployed", extra_params=extra
        )
        return [self._sanitize_device(i) for i in items], truncated

    async def list_scripts(
        self,
        project_id: str,
        *,
        device_id: str | None = None,
        name: str | None = None,
        script_type: str | None = None,
    ) -> tuple[list[ScriptInfo], bool]:
        extra: dict[str, Any] = {"projectId": project_id}
        if device_id:
            extra["deviceId"] = device_id
        if name:
            extra["name"] = name
        if script_type:
            extra["type"] = script_type
        items, truncated = await self._list_paginated("/device_scripts", extra_params=extra)
        return [self._sanitize_script(i) for i in items], truncated

    async def get_script(self, script_id: str) -> ScriptInfo:
        data = await self._t.request("get", f"/device_scripts/{script_id}")
        if not isinstance(data, dict):
            raise TopoApiError(f"unexpected script payload for {script_id}", path="/device_scripts")
        return self._sanitize_script(data)

    async def list_script_logs(
        self,
        project_id: str,
        *,
        script_id: str | None = None,
        device_id: str | None = None,
        mode: str | None = None,
        limit: int = 20,
    ) -> list[ScriptLog]:
        params: dict[str, Any] = {
            "projectId": project_id,
            "pageIndex": 1,
            "pageSize": max(1, min(limit, 100)),
            "scriptId": script_id,
            "deviceId": device_id,
            "mode": mode,
        }
        data = await self._t.request("get", "/device_scripts/logs", params=params)
        if isinstance(data, dict):
            items = data.get("items")
        elif isinstance(data, list):
            items = data
        else:
            items = None
        if not isinstance(items, list):
            return []
        return [self._sanitize_log(i) for i in items if isinstance(i, dict)]

    # ---- 写 ----

    async def create_private_script(
        self,
        *,
        project_id: str,
        device_id: str,
        name: str,
        content_b64: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "projectId": project_id,
            "deviceId": device_id,
            "name": name,
            "content": content_b64,
            "ready": True,
        }
        serialized = self._serialize_metadata(metadata)
        if serialized is not None:
            payload["metadata"] = serialized
        data = await self._t.request("post", "/device_scripts", json_obj=payload)
        return data if isinstance(data, dict) else {"id": _str_or_none(data)}

    async def mark_script_ready(self, *, script_id: str, device_id: str) -> None:
        """把指定脚本在该设备上置为 ready（run/private 会跑设备当前 ready 的私有脚本）。"""
        await self._t.request(
            "put",
            f"/device_scripts/{script_id}/ready",
            params={"deviceId": device_id},
        )

    async def run_private_scripts(self, *, device_ids: list[str], mode: str) -> Any:
        return await self._t.request(
            "post",
            "/device_scripts/run/private",
            params={"mode": mode},
            json_obj=device_ids,
        )

    # ---- 分页 ----

    async def _list_paginated(
        self, path: str, *, extra_params: dict[str, Any] | None = None
    ) -> tuple[list[dict[str, Any]], bool]:
        page_index = 1
        all_items: list[dict[str, Any]] = []
        total: int | None = None
        max_items = self._settings.max_items
        truncated = False
        while total is None or len(all_items) < total:
            params: dict[str, Any] = {
                "pageIndex": page_index,
                "pageSize": self._settings.api_page_size,
            }
            if extra_params:
                params.update(extra_params)
            data = await self._t.request("get", path, params=params)
            if not isinstance(data, dict):
                raise TopoApiError(f"unexpected paginated response for {path}", path=path)
            items = data.get("items") or []
            if not isinstance(items, list):
                raise TopoApiError(f"unexpected items payload for {path}", path=path)
            total = int(data.get("total") or len(items))
            all_items.extend(items)
            if not items:
                break
            if len(all_items) >= max_items:
                all_items = all_items[:max_items]
                truncated = True
                break
            page_index += 1
        return all_items, truncated

    # ---- 脱敏 ----

    @staticmethod
    def _sanitize_project(item: dict[str, Any]) -> ProjectInfo:
        return ProjectInfo(
            id=str(item.get("id")),
            name=str(item.get("name")),
            status=item.get("statusENName") or item.get("statusCHName") or item.get("status"),
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
            if not isinstance(address, dict):
                continue
            for ip_item in address.get("ips") or []:
                if isinstance(ip_item, dict) and ip_item.get("ipAddress"):
                    ip_addresses.append(str(ip_item["ipAddress"]))

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
            lastScriptName=router_script.get("scriptName") if isinstance(router_script, dict) else None,
            lastScriptStatus=router_script.get("status") if isinstance(router_script, dict) else None,
        )

    @classmethod
    def _sanitize_script(cls, item: dict[str, Any]) -> ScriptInfo:
        script_id = (
            item.get("id")
            or item.get("routerScriptId")
            or item.get("rangeRouterScriptId")
            or item.get("scriptId")
        )
        script_text = cls._decode_script_content(item.get("content"))
        return ScriptInfo(
            id=str(script_id),
            name=item.get("name") or item.get("routerScriptName"),
            projectId=_str_or_none(item.get("projectId")),
            projectName=item.get("projectName"),
            deviceId=_str_or_none(item.get("deviceId")),
            deviceName=item.get("deviceName") or item.get("instanceName") or item.get("useName"),
            type=item.get("type"),
            ready=item.get("ready"),
            created=item.get("created") or item.get("createdAt"),
            updated=item.get("updated") or item.get("updatedAt"),
            metadata=cls._normalize_metadata(item.get("metadata")),
            scriptHash=compute_script_hash(script_text) if script_text is not None else None,
            scriptSummary=summarize_script(script_text) if script_text is not None else None,
        )

    def _sanitize_log(self, item: dict[str, Any]) -> ScriptLog:
        maxlen = self._settings.log_msg_maxlen
        return ScriptLog(
            id=_str_or_none(item.get("id")),
            scriptId=_str_or_none(item.get("scriptId") or item.get("routerScriptId")),
            scriptName=item.get("scriptName") or item.get("routerScriptName"),
            deviceId=_str_or_none(item.get("deviceId")),
            deviceName=item.get("deviceName") or item.get("instanceName") or item.get("useName"),
            status=_str_or_none(item.get("status")),
            mode=_str_or_none(item.get("mode")),
            executeId=_str_or_none(item.get("executeId")),
            outMsg=truncate(item.get("outMsg"), maxlen),
            errMsg=truncate(item.get("errMsg"), maxlen),
            created=item.get("created") or item.get("createdAt"),
        )

    @staticmethod
    def _normalize_metadata(raw: Any) -> dict[str, str]:
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
        if isinstance(raw, list):
            normalized: dict[str, str] = {}
            for entry in raw:
                if isinstance(entry, dict) and entry.get("key") is not None:
                    normalized[str(entry["key"])] = "" if entry.get("value") is None else str(entry["value"])
            return normalized
        return {}

    @staticmethod
    def _serialize_metadata(metadata: dict[str, Any] | None) -> dict[str, str] | None:
        if not metadata:
            return None
        return {str(k): "" if v is None else str(v) for k, v in metadata.items()}

    @staticmethod
    def _decode_script_content(content_b64: Any) -> str | None:
        if not isinstance(content_b64, str) or not content_b64:
            return None
        try:
            return base64.b64decode(content_b64).decode("utf-8", errors="replace")
        except Exception:
            return None
