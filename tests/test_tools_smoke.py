from __future__ import annotations

from helpers import FakeTransport, make_settings

from topo_mcp.adapter import TopoApiAdapter
from topo_mcp.service import TopoService


async def test_session_status_without_cookie_reports_unauthenticated():
    settings = make_settings(cookie="")
    svc = TopoService(TopoApiAdapter(FakeTransport(lambda *a: None), settings), settings)
    status = await svc.session_status()
    assert status.authenticated is False
    assert status.source == "env"
    assert status.topoBaseUrl == "http://test/api/topo"


async def test_server_registers_nine_tools():
    from topo_mcp.server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert len(tools) == 9
    assert "topo_execute_script" in names
    assert "topo_prepare_script_execution" in names
    # 写工具不能把 ctx 暴露成入参
    execute = next(t for t in tools if t.name == "topo_execute_script")
    assert set(execute.inputSchema["properties"]) == {"plan_id", "confirm"}
