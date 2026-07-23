from __future__ import annotations

import base64

from helpers import FakeTransport, make_settings, paginate

from topo_mcp.adapter import TopoApiAdapter
from topo_mcp.security import compute_script_hash


async def test_pagination_caps_at_max_items():
    settings = make_settings(api_page_size=2, max_items=3)
    items = [{"id": f"p{i}", "name": f"n{i}"} for i in range(5)]

    def handler(method, path, params, body):
        assert path == "/projects"
        return paginate(items, params)

    adapter = TopoApiAdapter(FakeTransport(handler), settings)
    projects, truncated = await adapter.list_projects()
    assert len(projects) == 3
    assert truncated is True


async def test_full_list_not_truncated():
    settings = make_settings(api_page_size=2, max_items=100)
    items = [{"id": f"p{i}", "name": f"n{i}"} for i in range(3)]

    def handler(method, path, params, body):
        return paginate(items, params)

    adapter = TopoApiAdapter(FakeTransport(handler), settings)
    projects, truncated = await adapter.list_projects()
    assert [p.id for p in projects] == ["p0", "p1", "p2"]
    assert truncated is False


async def test_device_sanitize_extracts_ip_and_osfamily():
    settings = make_settings()
    device = {
        "id": "d1",
        "name": "win-dc",
        "projectId": "p1",
        "sysType": "Windows Server 2019",
        "addresses": [{"ips": [{"ipAddress": "10.0.0.5"}, {"ipAddress": "10.0.0.6"}]}],
        "routerScript": {"scriptName": "prev", "status": "success"},
    }

    def handler(method, path, params, body):
        return paginate([device], params)

    adapter = TopoApiAdapter(FakeTransport(handler), settings)
    devices, _ = await adapter.list_devices("p1")
    d = devices[0]
    assert d.osFamily == "windows"
    assert d.ipAddresses == ["10.0.0.5", "10.0.0.6"]
    assert d.lastScriptName == "prev"


async def test_script_sanitize_never_leaks_content_or_base64():
    settings = make_settings()
    b64 = base64.b64encode(b"echo hello").decode("ascii")

    def handler(method, path, params, body):
        return paginate([{"id": "s1", "name": "x", "projectId": "p1", "content": b64}], params)

    adapter = TopoApiAdapter(FakeTransport(handler), settings)
    scripts, _ = await adapter.list_scripts("p1")
    s = scripts[0]
    dumped = s.model_dump()
    # hash/摘要给出，但 base64 与 content/scriptText 字段绝不出现
    assert s.scriptHash == compute_script_hash("echo hello")
    assert s.scriptSummary
    assert "content" not in dumped
    assert "contentBase64" not in dumped
    assert "scriptText" not in dumped
    assert b64 not in str(dumped)
