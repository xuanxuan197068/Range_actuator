from __future__ import annotations

from datetime import datetime, timezone

from backend.topo_automation.schemas import InventoryDevice, InventoryProject, ProjectInventory
from backend.topo_automation.session import SessionManager
from backend.topo_automation.topo_adapter import TopoApiAdapter


class InventoryService:
    def __init__(self, session_manager: SessionManager, adapter: TopoApiAdapter) -> None:
        self._session_manager = session_manager
        self._adapter = adapter

    def build_inventory(self, project_id: str) -> ProjectInventory:
        cookie = self._session_manager.require_cookie()
        project_name = None
        for project in self._adapter.list_projects(cookie):
            if project.id == project_id:
                project_name = project.name
                break
        devices = [
            InventoryDevice(
                id=device.id,
                name=device.name,
                instanceName=device.instanceName,
                networkName=device.networkName,
                ipAddresses=device.ipAddresses,
                sysType=device.sysType,
                osFamily=device.osFamily,
                vmType=device.vmType,
                lastScriptName=device.lastScriptName,
                lastScriptStatus=device.lastScriptStatus,
            )
            for device in self._adapter.list_devices(cookie, project_id)
        ]
        return ProjectInventory(
            project=InventoryProject(id=project_id, name=project_name),
            generatedAt=datetime.now(timezone.utc),
            devices=devices,
        )
