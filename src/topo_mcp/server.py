from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import Context, FastMCP

from .adapter import TopoApiAdapter
from .models import (
    DeviceList,
    ExecuteResult,
    ExecutionPlan,
    LogList,
    ProjectInventory,
    ProjectList,
    ScriptInfo,
    ScriptList,
    SessionStatus,
)
from .service import TopoService
from .settings import Settings, get_settings
from .transport import AsyncTransport


@dataclass
class AppContext:
    settings: Settings
    transport: AsyncTransport
    service: TopoService


@asynccontextmanager
async def lifespan(_server: FastMCP) -> AsyncIterator[AppContext]:
    settings = get_settings()
    transport = AsyncTransport(settings)
    adapter = TopoApiAdapter(transport, settings)
    service = TopoService(adapter, settings)
    try:
        yield AppContext(settings=settings, transport=transport, service=service)
    finally:
        await transport.aclose()


mcp = FastMCP("topo", lifespan=lifespan)


def _svc(ctx: Context) -> TopoService:
    return ctx.request_context.lifespan_context.service


# ---- 只读工具 ----


@mcp.tool()
async def topo_session_status(ctx: Context) -> SessionStatus:
    """检查靶场登录状态：TOPO_COOKIE 是否有效、靶场是否可达。"""
    return await _svc(ctx).session_status()


@mcp.tool()
async def topo_list_projects(ctx: Context) -> ProjectList:
    """列出所有项目（自动翻页；超过上限会截断并置 truncated=true）。"""
    projects, truncated = await _svc(ctx).list_projects()
    return ProjectList(count=len(projects), truncated=truncated, projects=projects)


@mcp.tool()
async def topo_list_devices(
    ctx: Context,
    project_id: str,
    name: str | None = None,
    ip: str | None = None,
    sys_type: str | None = None,
) -> DeviceList:
    """列出项目下的已部署设备；可按 name / ip / sys_type 过滤。"""
    devices, truncated = await _svc(ctx).list_devices(
        project_id, name=name, ip=ip, sys_type=sys_type
    )
    return DeviceList(count=len(devices), truncated=truncated, devices=devices)


@mcp.tool()
async def topo_get_inventory(ctx: Context, project_id: str) -> ProjectInventory:
    """获取项目清单：项目信息 + 设备列表汇总。"""
    return await _svc(ctx).build_inventory(project_id)


@mcp.tool()
async def topo_list_scripts(
    ctx: Context,
    project_id: str,
    device_id: str | None = None,
    name: str | None = None,
    script_type: str | None = None,
) -> ScriptList:
    """列出项目下的脚本（只含元信息 + hash + 摘要，绝不含脚本内容/base64）。"""
    scripts, truncated = await _svc(ctx).list_scripts(
        project_id, device_id=device_id, name=name, script_type=script_type
    )
    return ScriptList(count=len(scripts), truncated=truncated, scripts=scripts)


@mcp.tool()
async def topo_get_script(ctx: Context, script_id: str) -> ScriptInfo:
    """查询单个脚本的元信息（不含脚本内容/base64，只给 hash + 摘要）。"""
    return await _svc(ctx).get_script(script_id)


@mcp.tool()
async def topo_list_script_logs(
    ctx: Context,
    project_id: str,
    script_id: str | None = None,
    device_id: str | None = None,
    mode: str | None = None,
    limit: int = 20,
) -> LogList:
    """查询脚本执行日志（过长的 outMsg/errMsg 会截断）。执行后按 projectId+scriptId 在此轮询真实输出。"""
    logs = await _svc(ctx).list_script_logs(
        project_id, script_id=script_id, device_id=device_id, mode=mode, limit=limit
    )
    return LogList(count=len(logs), logs=logs)


# ---- 写工具（两步：prepare → execute） ----


@mcp.tool()
async def topo_prepare_script_execution(
    ctx: Context,
    project_id: str,
    device_ids: list[str],
    script: str,
    language: str,
    mode: str | None = None,
    script_name: str | None = None,
) -> ExecutionPlan:
    """准备脚本执行：校验项目(白名单)/设备归属/OS 兼容性/脚本大小，计算 hash 并扫描危险关键词，返回含 planId 的执行计划。此步不触碰后端写接口。

    language: 'bash'(linux) | 'powershell'(windows)；mode: 'ssh' | 'qga'（默认 powershell→qga、bash→ssh）。
    拿到 planId 后调用 topo_execute_script 真正下发。
    """
    return await _svc(ctx).prepare(
        project_id=project_id,
        device_ids=device_ids,
        script_text=script,
        language=language,
        mode=mode,
        script_name=script_name,
    )


@mcp.tool()
async def topo_execute_script(ctx: Context, plan_id: str, confirm: bool = False) -> ExecuteResult:
    """执行 topo_prepare_script_execution 生成的计划：逐设备创建私有脚本 → 置 ready → run/private 下发。

    需 TOPO_ALLOW_EXECUTE=true 且 confirm=true 才会真正下发。同一 plan_id 幂等（重复调用返回首次结果，不重复下发）。
    下发后不阻塞等待，用 topo_list_script_logs 轮询结果。
    """
    return await _svc(ctx).execute(plan_id=plan_id, confirm=confirm)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
