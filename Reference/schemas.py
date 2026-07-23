from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class ProjectSelector(BaseModel):
    id: str | None = None
    name: str | None = None

    @model_validator(mode="after")
    def validate_selector(self) -> "ProjectSelector":
        if bool(self.id) == bool(self.name):
            raise ValueError("Provide exactly one of project.id or project.name.")
        return self


class TargetSelector(BaseModel):
    deviceIds: list[str] = Field(default_factory=list)
    deviceNames: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_targets(self) -> "TargetSelector":
        if bool(self.deviceIds) == bool(self.deviceNames):
            raise ValueError("Provide exactly one of targets.deviceIds or targets.deviceNames.")
        return self


class StageScriptSpec(BaseModel):
    language: Literal["bash", "powershell"]
    inline: str | None = None
    scriptFile: str | None = None

    @model_validator(mode="after")
    def validate_script_source(self) -> "StageScriptSpec":
        if bool(self.inline) == bool(self.scriptFile):
            raise ValueError("Provide exactly one of script.inline or scriptFile.")
        return self


class WorkflowStage(BaseModel):
    name: str
    targets: TargetSelector | None = None
    mode: Literal["ssh", "qga"] = "ssh"
    script: StageScriptSpec
    metadata: dict[str, Any] = Field(default_factory=dict)
    continueOnFailure: bool = False


class WorkflowManifest(BaseModel):
    version: int
    project: ProjectSelector
    targets: TargetSelector | None = None
    stages: list[WorkflowStage]

    @model_validator(mode="after")
    def validate_workflow(self) -> "WorkflowManifest":
        if self.version not in {1, 3}:
            raise ValueError("Only version 1 and version 3 manifests are supported.")
        if not self.stages:
            raise ValueError("Manifest must contain at least one stage.")
        if self.version == 1:
            if self.targets is None:
                raise ValueError("V1 requires root targets.")
            if len(self.stages) != 1:
                raise ValueError("V1 only supports exactly one stage.")
            if self.stages[0].targets is None:
                self.stages[0].targets = self.targets
            return self

        missing_targets = [stage.name for stage in self.stages if stage.targets is None]
        if missing_targets:
            raise ValueError(f"V3 requires targets on every stage: {', '.join(missing_targets)}")
        return self

    def targets_for_stage(self, stage: WorkflowStage) -> TargetSelector:
        selector = stage.targets if self.version == 3 else self.targets
        if selector is None:
            raise ValueError(f"Stage {stage.name} does not define targets.")
        return selector


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


class ProjectInfo(BaseModel):
    id: str
    name: str
    status: str | None = None
    vmCount: int | None = None
    updated: str | None = None


class ScriptPreview(BaseModel):
    scriptLanguage: Literal["bash", "powershell"]
    scriptHash: str
    scriptSummary: str
    riskKeywords: list[str] = Field(default_factory=list)
    mode: Literal["ssh", "qga"]
    scriptName: str


class StageExecutionPreview(BaseModel):
    stageName: str
    mode: Literal["ssh", "qga"]
    continueOnFailure: bool = False
    devices: list[DeviceInfo]
    preview: ScriptPreview
    warnings: list[str] = Field(default_factory=list)


class ExecutionPreview(BaseModel):
    project: ProjectInfo
    devices: list[DeviceInfo]
    stageName: str
    preview: ScriptPreview
    stagePreviews: list[StageExecutionPreview] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExecutionSubmitRequest(BaseModel):
    workflow: WorkflowManifest
    previewOnly: bool = False
    confirmRisk: bool = False


class SessionImportRequest(BaseModel):
    cookie: str


class SessionStatus(BaseModel):
    authenticated: bool
    source: str | None = None
    topoBaseUrl: str
    loginUrl: str
    loginSupported: bool = True
    validatedAt: str | None = None
    detail: str | None = None


class ManifestValidationResponse(BaseModel):
    workflow: WorkflowManifest
    preview: ExecutionPreview


class ScriptInfo(BaseModel):
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


class ScriptDetail(ScriptInfo):
    contentBase64: str | None = None
    scriptText: str | None = None


class ScriptUpdateRequest(BaseModel):
    projectId: str
    scriptText: str
    name: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    ready: bool | None = None


class ScriptReadyRequest(BaseModel):
    deviceId: str


class JobRecord(BaseModel):
    id: str
    status: str
    createdAt: datetime
    updatedAt: datetime
    projectId: str | None = None
    projectName: str | None = None
    preview: ExecutionPreview
    request: WorkflowManifest
    warnings: list[str] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None


class OperationJobRecord(BaseModel):
    id: str
    kind: Literal["deploy", "cancel", "reset", "execution"]
    status: str
    createdAt: datetime
    updatedAt: datetime
    projectId: str
    projectName: str | None = None
    remoteDeployId: str | None = None
    progress: dict[str, Any] = Field(default_factory=dict)
    rawRemotePayload: dict[str, Any] | list[Any] | str | None = None
    error: str | None = None


class InventoryProject(BaseModel):
    id: str
    name: str | None = None


class InventoryDevice(BaseModel):
    id: str
    name: str
    instanceName: str | None = None
    networkName: str | None = None
    ipAddresses: list[str] = Field(default_factory=list)
    sysType: str | None = None
    osFamily: Literal["linux", "windows", "unknown"] = "unknown"
    vmType: str | None = None
    lastScriptName: str | None = None
    lastScriptStatus: str | None = None


class ProjectInventory(BaseModel):
    project: InventoryProject
    generatedAt: datetime
    devices: list[InventoryDevice]
