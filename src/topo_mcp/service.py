from __future__ import annotations

import base64
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .adapter import TopoApiAdapter
from .models import (
    DeviceInfo,
    DevicePlan,
    ExecuteResult,
    ExecutionPlan,
    ProjectInfo,
    ProjectInventory,
    ScriptInfo,
    ScriptLog,
    ScriptSubmission,
    SessionStatus,
)
from .security import compute_script_hash, scan_risk_keywords, summarize_script
from .settings import Settings

_POLL_HINT = "用 topo_list_script_logs 按 projectId+scriptId 轮询执行结果，重点看 outMsg（不要只看 status=success）"


@dataclass
class _CachedPlan:
    plan_id: str
    project: ProjectInfo
    devices: list[DeviceInfo]
    script_text: str
    script_hash: str
    language: str
    mode: str
    script_name: str
    warnings: list[str] = field(default_factory=list)
    consumed: bool = False
    result: ExecuteResult | None = None


class TopoService:
    """业务层：读能力薄封装 adapter；写能力做 prepare/execute 两步 + 各项校验与幂等。"""

    def __init__(self, adapter: TopoApiAdapter, settings: Settings) -> None:
        self._adapter = adapter
        self._settings = settings
        self._plans: dict[str, _CachedPlan] = {}

    # ---- 读 ----

    async def session_status(self) -> SessionStatus:
        base = self._settings.base_url
        if not self._settings.cookie:
            return SessionStatus(
                authenticated=False, source="env", topoBaseUrl=base, detail="TOPO_COOKIE 未设置"
            )
        ok = await self._adapter.validate_cookie()
        return SessionStatus(
            authenticated=ok,
            source="env",
            topoBaseUrl=base,
            detail=None if ok else "Cookie 无效/已过期，或靶场不可达",
        )

    async def list_projects(self) -> tuple[list[ProjectInfo], bool]:
        return await self._adapter.list_projects()

    async def list_devices(
        self,
        project_id: str,
        *,
        name: str | None = None,
        ip: str | None = None,
        sys_type: str | None = None,
    ) -> tuple[list[DeviceInfo], bool]:
        return await self._adapter.list_devices(project_id, name=name, ip=ip, sys_type=sys_type)

    async def list_scripts(
        self,
        project_id: str,
        *,
        device_id: str | None = None,
        name: str | None = None,
        script_type: str | None = None,
    ) -> tuple[list[ScriptInfo], bool]:
        return await self._adapter.list_scripts(
            project_id, device_id=device_id, name=name, script_type=script_type
        )

    async def get_script(self, script_id: str) -> ScriptInfo:
        return await self._adapter.get_script(script_id)

    async def list_script_logs(
        self,
        project_id: str,
        *,
        script_id: str | None = None,
        device_id: str | None = None,
        mode: str | None = None,
        limit: int = 20,
    ) -> list[ScriptLog]:
        return await self._adapter.list_script_logs(
            project_id, script_id=script_id, device_id=device_id, mode=mode, limit=limit
        )

    async def build_inventory(self, project_id: str) -> ProjectInventory:
        projects, _ = await self._adapter.list_projects()
        project = next((p for p in projects if p.id == project_id), None)
        devices, _ = await self._adapter.list_devices(project_id)
        return ProjectInventory(
            project=project or ProjectInfo(id=project_id, name=project_id),
            generatedAt=datetime.now(timezone.utc),
            deviceCount=len(devices),
            devices=devices,
        )

    # ---- 写：准备 ----

    async def prepare(
        self,
        *,
        project_id: str,
        device_ids: list[str],
        script_text: str,
        language: str,
        mode: str | None = None,
        script_name: str | None = None,
    ) -> ExecutionPlan:
        if language not in ("bash", "powershell"):
            raise ValueError("language must be 'bash' or 'powershell'.")
        resolved_mode = (mode or ("qga" if language == "powershell" else "ssh")).lower()
        if resolved_mode not in ("ssh", "qga"):
            raise ValueError("mode must be 'ssh' or 'qga'.")

        project = await self._resolve_allowed_project(project_id)

        if not device_ids:
            raise ValueError("device_ids must not be empty.")
        if len(device_ids) > self._settings.max_devices_per_exec:
            raise ValueError(
                f"too many devices: {len(device_ids)} > TOPO_MAX_DEVICES_PER_EXEC="
                f"{self._settings.max_devices_per_exec}"
            )
        devices = await self._resolve_devices(project.id, device_ids)
        self._validate_compatibility(language, devices)

        script_bytes = len(script_text.encode("utf-8"))
        if script_bytes == 0:
            raise ValueError("script is empty.")
        if script_bytes > self._settings.max_script_bytes:
            raise ValueError(
                f"script too large: {script_bytes} bytes > TOPO_MAX_SCRIPT_BYTES="
                f"{self._settings.max_script_bytes}"
            )

        script_hash = compute_script_hash(script_text)
        risk = scan_risk_keywords(script_text, self._settings.risk_keywords)
        warnings = [f"matched risk keyword: {kw}" for kw in risk]
        name = script_name or f"mcp-{script_hash[:8]}"
        plan_id = uuid.uuid4().hex

        self._plans[plan_id] = _CachedPlan(
            plan_id=plan_id,
            project=project,
            devices=devices,
            script_text=script_text,
            script_hash=script_hash,
            language=language,
            mode=resolved_mode,
            script_name=name,
            warnings=warnings,
        )

        allow = self._settings.allow_execute
        note = (
            "调 topo_execute_script(plan_id, confirm=true) 执行。"
            if allow
            else "执行被禁用：设置 TOPO_ALLOW_EXECUTE=true 后才能 topo_execute_script。"
        )
        return ExecutionPlan(
            planId=plan_id,
            projectId=project.id,
            projectName=project.name,
            mode=resolved_mode,  # type: ignore[arg-type]
            language=language,  # type: ignore[arg-type]
            scriptName=name,
            scriptHash=script_hash,
            scriptSummary=summarize_script(script_text),
            scriptBytes=script_bytes,
            devices=[DevicePlan(id=d.id, name=d.name, osFamily=d.osFamily) for d in devices],
            riskKeywords=risk,
            warnings=warnings,
            allowExecute=allow,
            note=note,
        )

    # ---- 写：执行 ----

    async def execute(self, *, plan_id: str, confirm: bool) -> ExecuteResult:
        plan = self._plans.get(plan_id)
        if plan is None:
            raise ValueError(
                f"unknown or expired plan_id: {plan_id}. 先调 topo_prepare_script_execution。"
            )
        if plan.consumed:
            if plan.result is not None:
                return plan.result  # 幂等重放：同一 plan_id 不重复下发
            raise ValueError(f"plan {plan_id} 已在执行中或已消费。")
        if not self._settings.allow_execute:
            raise ValueError("执行被禁用：设置 TOPO_ALLOW_EXECUTE=true 后重试。")
        if not confirm:
            raise ValueError("执行需要显式 confirm=true。")

        # 先占用，避免并发重复执行
        plan.consumed = True
        warnings = list(plan.warnings)
        content_b64 = base64.b64encode(plan.script_text.encode("utf-8")).decode("ascii")

        submissions: list[ScriptSubmission] = []
        created_device_ids: list[str] = []
        for device in plan.devices:
            try:
                created = await self._adapter.create_private_script(
                    project_id=plan.project.id,
                    device_id=device.id,
                    name=plan.script_name,
                    content_b64=content_b64,
                    metadata={"source": "topo-mcp", "scriptHash": plan.script_hash},
                )
                script_id = created.get("id")
                script_id = None if script_id is None else str(script_id)
                submissions.append(
                    ScriptSubmission(
                        deviceId=device.id,
                        deviceName=device.name,
                        scriptId=script_id,
                        status="created",
                    )
                )
                created_device_ids.append(device.id)
            except Exception as exc:  # 网络/接口错误逐设备记录，不中断其它设备
                submissions.append(
                    ScriptSubmission(
                        deviceId=device.id,
                        deviceName=device.name,
                        status="create_failed",
                        error=str(exc),
                    )
                )

        if not created_device_ids:
            result = ExecuteResult(
                planId=plan_id,
                submitted=False,
                projectId=plan.project.id,
                mode=plan.mode,
                scripts=submissions,
                warnings=warnings + ["没有任何脚本创建成功，未下发。"],
                hint=_POLL_HINT,
            )
            plan.result = result
            return result

        # 下发前把「我们这份」显式置 ready，确定性收敛 run/private 竞态
        for sub in submissions:
            if sub.status == "created" and sub.scriptId:
                try:
                    await self._adapter.mark_script_ready(
                        script_id=sub.scriptId, device_id=sub.deviceId
                    )
                except Exception as exc:
                    warnings.append(f"设备 {sub.deviceId} 就绪确认失败：{exc}")

        dispatch = await self._adapter.run_private_scripts(
            device_ids=created_device_ids, mode=plan.mode
        )
        result = ExecuteResult(
            planId=plan_id,
            submitted=True,
            projectId=plan.project.id,
            mode=plan.mode,
            scripts=submissions,
            dispatch=dispatch,
            warnings=warnings,
            hint=_POLL_HINT,
        )
        plan.result = result
        return result

    # ---- 内部校验 ----

    async def _resolve_allowed_project(self, project_id: str) -> ProjectInfo:
        projects, _ = await self._adapter.list_projects()
        project = next((p for p in projects if p.id == project_id), None)
        if project is None:
            raise ValueError(f"project not found: {project_id}")
        allow = self._settings.allowlist
        if allow and project.id not in allow and project.name not in allow:
            raise ValueError(
                f"project {project.name} ({project.id}) 不在 TOPO_PROJECT_ALLOWLIST 内，禁止执行。"
            )
        return project

    async def _resolve_devices(self, project_id: str, device_ids: list[str]) -> list[DeviceInfo]:
        devices, _ = await self._adapter.list_devices(project_id)
        by_id = {d.id: d for d in devices}
        resolved: list[DeviceInfo] = []
        missing: list[str] = []
        for did in device_ids:
            if did in by_id:
                resolved.append(by_id[did])
            else:
                missing.append(did)
        if missing:
            raise ValueError(
                f"设备不属于项目 {project_id} 或不存在：{', '.join(missing)}"
            )
        return resolved

    @staticmethod
    def _validate_compatibility(language: str, devices: list[DeviceInfo]) -> None:
        expected = "linux" if language == "bash" else "windows"
        families = {d.osFamily for d in devices}
        if "unknown" in families:
            raise ValueError("部分设备无法识别操作系统类型，拒绝执行。")
        if len(families) != 1:
            raise ValueError("同一次执行不支持混合的操作系统类型。")
        only = next(iter(families))
        if only != expected:
            raise ValueError(f"脚本语言 {language} 与设备类型 {only} 不匹配。")
