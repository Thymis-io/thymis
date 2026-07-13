"""Pydantic argument models for Thymis agent tools."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field
from thymis_controller.models.device import UpdateDeploymentInfo
from thymis_controller.models.device_metric import MetricGranularity
from thymis_controller.models.secrets import SecretCreateRequest, SecretUpdateRequest
from thymis_controller.models.state import State

from .registry import ToolArguments


class EmptyArguments(ToolArguments):
    pass


class UpdateStateArguments(ToolArguments):
    state: State = Field(description="The complete replacement controller state.")


class DeploymentInfoArguments(ToolArguments):
    deployment_info_id: UUID


class UpdateDeploymentInfoArguments(DeploymentInfoArguments):
    changes: UpdateDeploymentInfo


class ListTasksArguments(ToolArguments):
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class TaskArguments(ToolArguments):
    task_id: UUID


class CreateSecretArguments(ToolArguments):
    secret: SecretCreateRequest


class UpdateSecretArguments(ToolArguments):
    secret_id: UUID
    changes: SecretUpdateRequest


class SecretArguments(ToolArguments):
    secret_id: UUID


class UploadArtifact(ToolArguments):
    name: str = Field(description="Artifact file name, without a directory component.")
    content_base64: str = Field(description="Base64-encoded artifact content.")


class UploadArtifactsArguments(ToolArguments):
    artifacts: list[UploadArtifact] = Field(min_length=1)


class ArtifactArguments(ToolArguments):
    name: str


class RenameArtifactArguments(ArtifactArguments):
    new_name: str


class DiffArguments(ToolArguments):
    ref_a: str | None = None
    ref_b: str | None = None


class LogArguments(DeploymentInfoArguments):
    from_datetime: str | None = Field(
        default=None, description="ISO 8601 timestamp, inclusive."
    )
    to_datetime: str | None = Field(
        default=None, description="ISO 8601 timestamp, exclusive."
    )
    program_name: str | None = None
    exact_program_name: bool = False
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class DeviceMetricsArguments(DeploymentInfoArguments):
    hours: int = Field(default=24, ge=1, le=168)
    granularity: MetricGranularity = MetricGranularity.one_hour


class FleetRangeArguments(ToolArguments):
    hours: int = Field(default=24, ge=1, le=2160)
    buckets: int = Field(default=48, ge=1, le=200)


class UpdateControllerSettingsArguments(ToolArguments):
    auto_update_enabled: bool | None = None
    auto_update_schedule: dict[str, Any] | None = None


class ExternalRepositoryArguments(ToolArguments):
    flake_name: str


class BuildImageArguments(ToolArguments):
    identifier: str


class DeployArguments(ToolArguments):
    config_identifiers: list[str] = Field(default_factory=list)
    deployment_info_ids: list[UUID] = Field(default_factory=list)


class RestartDeviceArguments(ToolArguments):
    identifier: str


class SwitchConfigArguments(DeploymentInfoArguments):
    new_config_id: str


class RunDeviceCommandArguments(DeploymentInfoArguments):
    command: str = Field(
        min_length=1,
        description="Shell command to run as root on the connected NixOS device.",
    )


class CommitArguments(ToolArguments):
    message: str = Field(min_length=1)
