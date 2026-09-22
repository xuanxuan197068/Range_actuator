from __future__ import annotations

import pytest

from helpers import FakeTransport, make_settings, paginate

from topo_mcp.adapter import TopoApiAdapter
from topo_mcp.service import TopoService


def _device(dev_id: str, name: str, sys_type: str, cloud: str | None, image: str | None) -> dict:
    return {
        "id": dev_id,
        "name": name,
        "projectId": "p1",
        "sysType": sys_type,
        "addresses": [{"ips": [{"ipAddress": "10.0.0.1"}]}],
        "cloudId": cloud,
        "imageId": image,
        "imageName": "ubuntu_docker",
    }


def _project() -> dict:
    return {"items": [{"id": "p1", "name": "proj"}], "total": 1}


@pytest.fixture
def env():
    def handler(method, path, params, body):
        if path == "/projects":
            return _project()
        if path == "/device_scripts/devices/deployed":
            return paginate(
                [
                    _device("V1", "srv-linux", "ubuntu", "cloud-1", "img-1"),
                    _device("V2", "dc-win", "Windows Server 2019", "cloud-2", "img-2"),
                    _device("V3", "broken", "ubuntu", None, None),
                ],
                params,
            )
        if path == "/vm/create/image" and method == "POST":
            return "new-image-id-" + str(body.get("vmOsId"))
        if path == "/image/list" and method == "POST":
            return {"items": [{"id": "i1", "imageName": "n1", "status": "active"}]}
        raise AssertionError(f"unexpected {method} {path}")

    transport = FakeTransport(handler)
    settings = make_settings()
    adapter = TopoApiAdapter(transport, settings)
    service = TopoService(adapter, settings)
    return transport, service


async def test_prepare_builds_correct_payloads(env):
    _, svc = env
    plan = await svc.prepare_image_export(
        project_id="p1",
        images=[
            {"deviceId": "V1", "imageName": "路径1—srv—Redis", "minRam": 2048},
            {"deviceId": "V2", "imageName": "路径8—dc—域控"},
        ],
    )
    assert len(plan.items) == 2
    linux = plan.items[0].payload
    assert linux["osType"] == "linux" and linux["qga"] is False
    assert linux["vmOsId"] == "cloud-1" and linux["tempId"] == "img-1"
    assert linux["accessList"][0]["accessType"] == "ssh"
    win = plan.items[1].payload
    assert win["osType"] == "windows" and win["qga"] is True
    assert win["minRam"] == "4096"
    assert win["accessList"][0]["accessType"] == "rdp"
    assert win["profileId"] == "32" and win["nodeType"] == "vm"


async def test_prepare_rejects_undeployed_and_duplicate_names(env):
    _, svc = env
    with pytest.raises(ValueError, match="cloudId/imageId"):
        await svc.prepare_image_export(project_id="p1", images=[{"deviceId": "V3", "imageName": "x"}])
    with pytest.raises(ValueError, match="重复"):
        await svc.prepare_image_export(
            project_id="p1",
            images=[
                {"deviceId": "V1", "imageName": "same"},
                {"deviceId": "V2", "imageName": "same"},
            ],
        )


async def test_execute_requires_confirm_and_is_idempotent(env):
    transport, svc = env
    plan = await svc.prepare_image_export(
        project_id="p1", images=[{"deviceId": "V1", "imageName": "n"}]
    )
    with pytest.raises(ValueError, match="confirm"):
        await svc.execute_image_export(plan_id=plan.planId, confirm=False)
    result = await svc.execute_image_export(plan_id=plan.planId, confirm=True)
    assert result.exported is True
    assert result.results[0].newImageId == "new-image-id-cloud-1"
    create_calls = [c for c in transport.calls if c["path"] == "/vm/create/image"]
    assert len(create_calls) == 1  # 幂等
    replay = await svc.execute_image_export(plan_id=plan.planId, confirm=True)
    assert replay.results[0].status == "submitted"
    assert len([c for c in transport.calls if c["path"] == "/vm/create/image"]) == 1


async def test_execute_continues_after_single_failure(env):
    transport, svc = env
    plan = await svc.prepare_image_export(
        project_id="p1",
        images=[
            {"deviceId": "V1", "imageName": "a"},
            {"deviceId": "V2", "imageName": "b"},
        ],
    )
    orig = transport.request

    async def flaky(method, path, *, params=None, json_obj=None, base_url=None):
        if path == "/vm/create/image" and json_obj and json_obj.get("imageName") == "a":
            raise RuntimeError("boom")
        return await orig(method, path, params=params, json_obj=json_obj, base_url=base_url)

    transport.request = flaky  # type: ignore[method-assign]
    result = await svc.execute_image_export(plan_id=plan.planId, confirm=True)
    assert result.results[0].status == "failed"
    assert result.results[1].status == "submitted"
    assert result.exported is True


async def test_list_images(env):
    _, svc = env
    images = await svc.list_images()
    assert images.count == 1 and images.images[0].status == "active"
