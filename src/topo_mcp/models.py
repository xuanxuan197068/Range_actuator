from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---- 会话 ----


class SessionStatus(BaseModel):
    authenticated: bool
    source: str
    topoBaseUrl: str
    detail: str | None = None


# ---- 项目 / 设备 / 脚本 / 日志（读） ----


class ProjectInfo(BaseModel):
    id: str
    name: str
    status: str | None = None
    vmCount: int | None = None
    updated: str | None = None


class DeviceInfo(BaseModel):
    id: str
    name: str
    projectId: str
    projectName: str | None = None
    sysType: str | None = None
    osFamily: Literal["linux", "windows", "unknown"] = "unknown"
    vmType: str | None = None
    instanceName: str | None = None
    networkName: str | None = None
    ipAddresses: list[str] = Field(default_factory=list)
    lastScriptName: str | None = None
    lastScriptStatus: str | None = None


class ScriptInfo(BaseModel):
    """脚本元信息 —— 永不含 base64 / 明文，只给 hash + 摘要。"""

    id: str
    name: str | None = None
    projectId: str | None = None
    projectName: str | None = None
    deviceId: str | None = None
    deviceName: str | None = None
    type: str | None = None
    ready: bool | None = None
    created: str | None = None
    updated: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    scriptHash: str | None = None
    scriptSummary: str | None = None


class ScriptLog(BaseModel):
    id: str | None = None
    scriptId: str | None = None
    scriptName: str | None = None
    deviceId: str | None = None
    deviceName: str | None = None
    status: str | None = None
    mode: str | None = None
    executeId: str | None = None
    outMsg: str | None = None
    errMsg: str | None = None
    created: str | None = None


class ProjectInventory(BaseModel):
    project: ProjectInfo
    generatedAt: datetime
    deviceCount: int
    devices: list[DeviceInfo]


# ---- 列表包装（带截断标记） ----


class ProjectList(BaseModel):
    count: int
    truncated: bool = False
    projects: list[ProjectInfo]


class DeviceList(BaseModel):
    count: int
    truncated: bool = False
    devices: list[DeviceInfo]


class ScriptList(BaseModel):
    count: int
    truncated: bool = False
    scripts: list[ScriptInfo]


class LogList(BaseModel):
    count: int
    logs: list[ScriptLog]


# ---- 执行（写） ----


class DevicePlan(BaseModel):
    id: str
    name: str
    osFamily: str


class ExecutionPlan(BaseModel):
    planId: str
    projectId: str
    projectName: str | None = None
    mode: Literal["ssh", "qga"]
    language: Literal["bash", "powershell"]
    scriptName: str
    scriptHash: str
    scriptSummary: str
    scriptBytes: int
    devices: list[DevicePlan]
    riskKeywords: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    allowExecute: bool
    note: str


class ScriptSubmission(BaseModel):
    deviceId: str
    deviceName: str | None = None
    scriptId: str | None = None
    status: str
    error: str | None = None


class ExecuteResult(BaseModel):
    planId: str
    submitted: bool
    projectId: str
    mode: str
    scripts: list[ScriptSubmission]
    dispatch: Any | None = None
    warnings: list[str] = Field(default_factory=list)
    hint: str
