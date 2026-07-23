from __future__ import annotations

import pytest
from helpers import FakeTransport, make_settings, paginate

from topo_mcp.adapter import TopoApiAdapter
from topo_mcp.service import TopoService

_PROJECTS = [{"id": "p1", "name": "Proj"}]
_DEVICES = [{"id": "d1", "name": "win1", "projectId": "p1", "sysType": "windows"}]


def _handler(created_id: str = "s1"):
    def handler(method, path, params, body):
        if method == "GET" and path == "/projects":
            return paginate(_PROJECTS, params)
        if method == "GET" and path == "/device_scripts/devices/deployed":
            return paginate(_DEVICES, params)
        if method == "POST" and path == "/device_scripts":
            return {"id": created_id}
        if method == "PUT" and path.endswith("/ready"):
            return None
        if method == "POST" and path == "/device_scripts/run/private":
            return [{"deviceId": body[0], "status": "dispatching"}]
        raise AssertionError(f"unexpected call {method} {path}")

    return handler


def _service(settings=None, handler=None):
    settings = settings or make_settings()
    transport = FakeTransport(handler or _handler())
    return TopoService(TopoApiAdapter(transport, settings), settings), transport


async def test_prepare_derives_mode_and_hash():
    svc, _ = _service()
    plan = await svc.prepare(
        project_id="p1", device_ids=["d1"], script_text="whoami", language="powershell"
    )
    assert plan.mode == "qga"  # powershell 默认 qga
    assert plan.language == "powershell"
    assert plan.allowExecute is True
    assert plan.scriptHash and plan.scriptBytes == len(b"whoami")
    assert [d.id for d in plan.devices] == ["d1"]


async def test_execute_dispatches_and_is_idempotent():
    svc, transport = _service()
    plan = await svc.prepare(
        project_id="p1", device_ids=["d1"], script_text="whoami", language="powershell"
    )
    r1 = await svc.execute(plan_id=plan.planId, confirm=True)
    assert r1.submitted is True
    assert r1.scripts[0].scriptId == "s1"
    runs = transport.calls_to("POST", "/device_scripts/run/private")
    assert len(runs) == 1
    assert runs[0]["json"] == ["d1"]
    assert runs[0]["params"].get("mode") == "qga"
    # 就绪确认发生在下发之前
    assert transport.calls_to("PUT", "/device_scripts/s1/ready")

    # 幂等重放：同一 plan_id 不再创建/下发
    r2 = await svc.execute(plan_id=plan.planId, confirm=True)
    assert r2 is r1
    assert len(transport.calls_to("POST", "/device_scripts")) == 1
    assert len(transport.calls_to("POST", "/device_scripts/run/private")) == 1


async def test_execute_requires_allow_flag():
    svc, _ = _service(settings=make_settings(allow_execute=False))
    plan = await svc.prepare(
        project_id="p1", device_ids=["d1"], script_text="whoami", language="powershell"
    )
    with pytest.raises(ValueError, match="TOPO_ALLOW_EXECUTE"):
        await svc.execute(plan_id=plan.planId, confirm=True)


async def test_execute_requires_confirm():
    svc, _ = _service()
    plan = await svc.prepare(
        project_id="p1", device_ids=["d1"], script_text="whoami", language="powershell"
    )
    with pytest.raises(ValueError, match="confirm"):
        await svc.execute(plan_id=plan.planId, confirm=False)
    # confirm=False 不应消费计划，之后仍可正常执行
    r = await svc.execute(plan_id=plan.planId, confirm=True)
    assert r.submitted is True


async def test_prepare_rejects_foreign_device():
    svc, _ = _service()
    with pytest.raises(ValueError, match="不属于项目"):
        await svc.prepare(
            project_id="p1", device_ids=["ghost"], script_text="x", language="powershell"
        )


async def test_prepare_rejects_os_mismatch():
    svc, _ = _service()
    with pytest.raises(ValueError, match="不匹配"):
        await svc.prepare(project_id="p1", device_ids=["d1"], script_text="x", language="bash")


async def test_prepare_respects_allowlist():
    svc, _ = _service(settings=make_settings(project_allowlist="other-project"))
    with pytest.raises(ValueError, match="ALLOWLIST"):
        await svc.prepare(
            project_id="p1", device_ids=["d1"], script_text="x", language="powershell"
        )


async def test_prepare_enforces_device_cap():
    svc, _ = _service(settings=make_settings(max_devices_per_exec=1))
    # 两个设备超过上限（用同一 id 触发数量校验即可）
    with pytest.raises(ValueError, match="too many devices"):
        await svc.prepare(
            project_id="p1", device_ids=["d1", "d1"], script_text="x", language="powershell"
        )
