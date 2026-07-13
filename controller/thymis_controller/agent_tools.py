"""Provider-neutral tools for agents that manage a Thymis controller.

The frontend already defines the controller's user-facing operations.  This module
exposes the same operations as typed, discoverable Python tools without coupling
future agents to a particular LLM SDK.  It deliberately calls the authenticated
HTTP API: an agent gets exactly the authorization and validation boundary that a
browser session gets.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field
from thymis_controller.models.device import UpdateDeploymentInfo
from thymis_controller.models.secrets import SecretCreateRequest, SecretUpdateRequest
from thymis_controller.models.state import State

JSONValue = dict[str, Any] | list[Any] | str | int | float | bool | None


class ToolArguments(BaseModel):
    """Base model for arguments accepted by an agent tool."""

    model_config = ConfigDict(extra="forbid")


class EmptyArguments(ToolArguments):
    pass


class UpdateStateArguments(ToolArguments):
    state: State = Field(description="The complete replacement controller state.")


class GetDeploymentInfoArguments(ToolArguments):
    deployment_info_id: UUID


class UpdateDeploymentInfoArguments(ToolArguments):
    deployment_info_id: UUID
    changes: UpdateDeploymentInfo


class DeleteDeploymentInfoArguments(ToolArguments):
    deployment_info_id: UUID


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


class DeleteSecretArguments(ToolArguments):
    secret_id: UUID


class UploadArtifact(ToolArguments):
    name: str = Field(description="Artifact file name, without a directory component.")
    content_base64: str = Field(description="Base64-encoded artifact content.")


class UploadArtifactsArguments(ToolArguments):
    artifacts: list[UploadArtifact] = Field(min_length=1)


class ArtifactArguments(ToolArguments):
    name: str


class RenameArtifactArguments(ToolArguments):
    name: str
    new_name: str


class DiffArguments(ToolArguments):
    ref_a: str | None = None
    ref_b: str | None = None


class LogArguments(ToolArguments):
    deployment_info_id: UUID
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


class DeploymentInfoArguments(ToolArguments):
    deployment_info_id: UUID


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


class SwitchConfigArguments(ToolArguments):
    deployment_info_id: UUID
    new_config_id: str


class CommitArguments(ToolArguments):
    message: str = Field(min_length=1)


class ToolDefinition(BaseModel):
    """A provider-neutral function-tool definition.

    ``input_schema`` is JSON Schema and can be passed directly to an LLM SDK's
    function/tool adapter.
    """

    name: str
    description: str
    input_schema: dict[str, Any]


class UnknownToolError(ValueError):
    """Raised when a caller asks for a tool that is not registered."""


class ThymisToolError(RuntimeError):
    """An API failure with enough context for an agent to recover safely."""

    def __init__(self, status_code: int, method: str, path: str, detail: Any):
        self.status_code = status_code
        self.method = method
        self.path = path
        self.detail = detail
        super().__init__(f"{method} {path} failed with {status_code}: {detail}")


@dataclass(frozen=True)
class _Tool:
    name: str
    description: str
    arguments_type: type[ToolArguments]
    handler: Callable[[ToolArguments], Awaitable[JSONValue]]

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.arguments_type.model_json_schema(),
        )


class ThymisTools:
    """Typed operations available to an authenticated Thymis agent.

    The caller owns the supplied ``httpx.AsyncClient`` and its authentication
    cookies.  This makes tool authorization identical to the API session used by
    the caller and avoids a second authorization model for agents.
    """

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._tools = {tool.name: tool for tool in self._build_tools()}

    def definitions(self) -> list[ToolDefinition]:
        """Return the complete tool catalogue for an agent runtime."""
        return [tool.definition() for tool in self._tools.values()]

    async def invoke(
        self, name: str, arguments: Mapping[str, Any] | None = None
    ) -> JSONValue:
        """Validate and execute one named tool call."""
        tool = self._tools.get(name)
        if tool is None:
            raise UnknownToolError(f"Unknown Thymis tool: {name}")
        parsed_arguments = tool.arguments_type.model_validate(arguments or {})
        return await tool.handler(parsed_arguments)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: list[tuple[str, str]] | dict[str, Any] | None = None,
        json: JSONValue = None,
        files: Any = None,
    ) -> JSONValue:
        response = await self._client.request(
            method, path, params=params, json=json, files=files
        )
        if response.is_error:
            try:
                body = response.json()
                detail = body.get("detail", body) if isinstance(body, dict) else body
            except ValueError:
                detail = response.text
            raise ThymisToolError(response.status_code, method, path, detail)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def _build_tools(self) -> tuple[_Tool, ...]:
        return (
            _Tool(
                "get_state",
                "Read the complete Thymis configuration state, including configurations, tags, and repositories.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/state"),
            ),
            _Tool(
                "update_state",
                "Replace the complete Thymis configuration state. Read the state first, preserve unrelated fields, then commit before deployment.",
                UpdateStateArguments,
                self._update_state,
            ),
            _Tool(
                "list_available_modules",
                "List all available NixOS module definitions and their configurable settings.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/available_modules"),
            ),
            _Tool(
                "list_deployment_infos",
                "List every registered device with connection, deployment, and metadata state.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/all_deployment_infos"),
            ),
            _Tool(
                "get_deployment_info",
                "Get one registered device by deployment-info ID.",
                GetDeploymentInfoArguments,
                self._get_deployment_info,
            ),
            _Tool(
                "update_deployment_info",
                "Update device metadata such as name, location, notes, archive status, or configured host details.",
                UpdateDeploymentInfoArguments,
                self._update_deployment_info,
            ),
            _Tool(
                "delete_deployment_info",
                "Permanently remove a registered device from the controller.",
                DeleteDeploymentInfoArguments,
                self._delete_deployment_info,
            ),
            _Tool(
                "list_tasks",
                "List background build, deployment, and device-command tasks.",
                ListTasksArguments,
                self._list_tasks,
            ),
            _Tool(
                "get_task",
                "Get detailed status and output for one background task.",
                TaskArguments,
                self._get_task,
            ),
            _Tool(
                "cancel_task",
                "Cancel one pending or running background task.",
                TaskArguments,
                self._cancel_task,
            ),
            _Tool(
                "retry_task",
                "Retry a failed background task.",
                TaskArguments,
                self._retry_task,
            ),
            _Tool(
                "list_secrets",
                "List configured secrets. Responses follow the authenticated controller API and may contain non-file secret text.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/secrets"),
            ),
            _Tool(
                "create_secret",
                "Create a secret. Supply either value_str or value_b64 in the nested secret payload.",
                CreateSecretArguments,
                self._create_secret,
            ),
            _Tool(
                "update_secret",
                "Update secret metadata or value. Only explicitly supplied nested fields are sent.",
                UpdateSecretArguments,
                self._update_secret,
            ),
            _Tool(
                "delete_secret",
                "Permanently delete one secret.",
                DeleteSecretArguments,
                self._delete_secret,
            ),
            _Tool(
                "list_artifacts",
                "List uploaded configuration artifacts.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/artifacts"),
            ),
            _Tool(
                "upload_artifacts",
                "Upload one or more base64-encoded artifacts for configuration modules to reference.",
                UploadArtifactsArguments,
                self._upload_artifacts,
            ),
            _Tool(
                "rename_artifact",
                "Rename an artifact and update state references to its old name.",
                RenameArtifactArguments,
                self._rename_artifact,
            ),
            _Tool(
                "delete_artifact",
                "Permanently delete one artifact.",
                ArtifactArguments,
                self._delete_artifact,
            ),
            _Tool(
                "get_history",
                "Read the configuration repository commit history.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/history"),
            ),
            _Tool(
                "get_history_diff",
                "Read the repository diff between two optional revisions.",
                DiffArguments,
                self._get_history_diff,
            ),
            _Tool(
                "get_repo_status",
                "Read uncommitted configuration repository changes.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/repo_status"),
            ),
            _Tool(
                "get_logs",
                "Query structured device logs with optional time and program filters.",
                LogArguments,
                self._get_logs,
            ),
            _Tool(
                "list_log_program_names",
                "List program names present in a device's logs.",
                DeploymentInfoArguments,
                self._list_log_program_names,
            ),
            _Tool(
                "get_fleet_connectivity",
                "Get fleet connectivity time series for a bounded time range.",
                FleetRangeArguments,
                self._get_fleet_connectivity,
            ),
            _Tool(
                "get_fleet_metrics_latest",
                "Get the latest resource metrics for every reporting device.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/fleet/metrics/latest"),
            ),
            _Tool(
                "get_fleet_availability",
                "Get fleet availability buckets for a bounded time range.",
                FleetRangeArguments,
                self._get_fleet_availability,
            ),
            _Tool(
                "get_fleet_alerts",
                "List active fleet alerts.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/fleet/alerts"),
            ),
            _Tool(
                "get_controller_settings",
                "Read automatic update settings and schedule.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/controller-settings"),
            ),
            _Tool(
                "update_controller_settings",
                "Update automatic update enablement and/or schedule.",
                UpdateControllerSettingsArguments,
                self._update_controller_settings,
            ),
            _Tool(
                "get_external_repository_status",
                "Read synchronization status for configured external flake repositories.",
                EmptyArguments,
                lambda _: self._request("GET", "/api/external-repositories/status"),
            ),
            _Tool(
                "get_external_repository_flake_ref",
                "Parse and return the flake reference for one configured external repository.",
                ExternalRepositoryArguments,
                self._get_external_repository_flake_ref,
            ),
            _Tool(
                "build_project",
                "Queue a build of the current configuration project.",
                EmptyArguments,
                lambda _: self._request("POST", "/api/action/build"),
            ),
            _Tool(
                "deploy",
                "Queue deployment of selected configurations and/or devices. The repository must be clean and selected devices must be connected.",
                DeployArguments,
                self._deploy,
            ),
            _Tool(
                "build_device_image",
                "Queue a bootable image build for one configuration. The repository must be clean.",
                BuildImageArguments,
                self._build_device_image,
            ),
            _Tool(
                "restart_device",
                "Queue a reboot for connected devices using one configuration identifier.",
                RestartDeviceArguments,
                self._restart_device,
            ),
            _Tool(
                "switch_device_config",
                "Switch a connected device to a compatible configuration and deploy it immediately. The repository must be clean.",
                SwitchConfigArguments,
                self._switch_device_config,
            ),
            _Tool(
                "commit",
                "Commit current configuration repository changes with a message.",
                CommitArguments,
                self._commit,
            ),
            _Tool(
                "update_project",
                "Queue an update of project flake inputs.",
                EmptyArguments,
                lambda _: self._request("POST", "/api/action/update"),
            ),
            _Tool(
                "auto_update",
                "Queue the controller's automatic update workflow for connected devices.",
                EmptyArguments,
                lambda _: self._request("POST", "/api/action/auto-update"),
            ),
        )

    async def _update_state(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, UpdateStateArguments)
        return await self._request(
            "PATCH", "/api/state", json=arguments.state.model_dump(mode="json")
        )

    async def _get_deployment_info(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, GetDeploymentInfoArguments)
        return await self._request(
            "GET", f"/api/deployment_info/{arguments.deployment_info_id}"
        )

    async def _update_deployment_info(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, UpdateDeploymentInfoArguments)
        return await self._request(
            "PATCH",
            f"/api/deployment_info/{arguments.deployment_info_id}",
            json=arguments.changes.model_dump(exclude_unset=True, mode="json"),
        )

    async def _delete_deployment_info(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, DeleteDeploymentInfoArguments)
        return await self._request(
            "DELETE", f"/api/deployment_info/{arguments.deployment_info_id}"
        )

    async def _list_tasks(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, ListTasksArguments)
        return await self._request(
            "GET",
            "/api/tasks",
            params={"limit": arguments.limit, "offset": arguments.offset},
        )

    async def _get_task(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, TaskArguments)
        return await self._request("GET", f"/api/tasks/{arguments.task_id}")

    async def _cancel_task(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, TaskArguments)
        return await self._request("POST", f"/api/tasks/{arguments.task_id}/cancel")

    async def _retry_task(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, TaskArguments)
        return await self._request("POST", f"/api/tasks/{arguments.task_id}/retry")

    async def _create_secret(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, CreateSecretArguments)
        return await self._request(
            "POST", "/api/secrets", json=arguments.secret.model_dump(mode="json")
        )

    async def _update_secret(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, UpdateSecretArguments)
        return await self._request(
            "PATCH",
            f"/api/secrets/{arguments.secret_id}",
            json=arguments.changes.model_dump(exclude_unset=True, mode="json"),
        )

    async def _delete_secret(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, DeleteSecretArguments)
        return await self._request("DELETE", f"/api/secrets/{arguments.secret_id}")

    async def _upload_artifacts(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, UploadArtifactsArguments)
        files = []
        for artifact in arguments.artifacts:
            try:
                content = base64.b64decode(artifact.content_base64, validate=True)
            except binascii.Error as error:
                raise ValueError(
                    f"Artifact '{artifact.name}' is not valid base64"
                ) from error
            files.append(
                ("files", (artifact.name, content, "application/octet-stream"))
            )
        return await self._request("POST", "/api/artifacts/", files=files)

    async def _rename_artifact(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, RenameArtifactArguments)
        return await self._request(
            "POST",
            f"/api/artifacts/rename/{arguments.name}",
            params={"new_name": arguments.new_name},
        )

    async def _delete_artifact(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, ArtifactArguments)
        return await self._request("DELETE", f"/api/artifacts/{arguments.name}")

    async def _get_history_diff(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, DiffArguments)
        params = {
            key: value
            for key, value in (("refA", arguments.ref_a), ("refB", arguments.ref_b))
            if value is not None
        }
        return await self._request("GET", "/api/history/diff", params=params)

    async def _get_logs(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, LogArguments)
        params = {
            "exact_program_name": str(arguments.exact_program_name).lower(),
            "limit": arguments.limit,
            "offset": arguments.offset,
        }
        if arguments.from_datetime is not None:
            params["from_datetime"] = arguments.from_datetime
        if arguments.to_datetime is not None:
            params["to_datetime"] = arguments.to_datetime
        if arguments.program_name is not None:
            params["program_name"] = arguments.program_name
        return await self._request(
            "GET", f"/api/logs/{arguments.deployment_info_id}", params=params
        )

    async def _list_log_program_names(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, DeploymentInfoArguments)
        return await self._request(
            "GET", f"/api/logs/{arguments.deployment_info_id}/program-names"
        )

    async def _get_fleet_connectivity(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, FleetRangeArguments)
        return await self._request(
            "GET",
            "/api/fleet/connectivity",
            params={"hours": arguments.hours, "buckets": arguments.buckets},
        )

    async def _get_fleet_availability(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, FleetRangeArguments)
        return await self._request(
            "GET",
            "/api/fleet/availability",
            params={"hours": arguments.hours, "buckets": arguments.buckets},
        )

    async def _update_controller_settings(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, UpdateControllerSettingsArguments)
        return await self._request(
            "PATCH",
            "/api/controller-settings",
            json=arguments.model_dump(exclude_unset=True, mode="json"),
        )

    async def _get_external_repository_flake_ref(
        self, arguments: ToolArguments
    ) -> JSONValue:
        assert isinstance(arguments, ExternalRepositoryArguments)
        return await self._request(
            "GET", f"/api/external-repositories/flake-ref/{arguments.flake_name}"
        )

    async def _deploy(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, DeployArguments)
        params = [("config", identifier) for identifier in arguments.config_identifiers]
        params.extend(
            ("deployment_info_id", str(deployment_info_id))
            for deployment_info_id in arguments.deployment_info_ids
        )
        return await self._request("POST", "/api/action/deploy", params=params)

    async def _build_device_image(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, BuildImageArguments)
        return await self._request(
            "POST",
            "/api/action/build-download-image",
            params={"identifier": arguments.identifier},
        )

    async def _restart_device(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, RestartDeviceArguments)
        return await self._request(
            "POST",
            "/api/action/restart-device",
            params={"identifier": arguments.identifier},
        )

    async def _switch_device_config(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, SwitchConfigArguments)
        return await self._request(
            "POST",
            "/api/action/switch-config",
            params={
                "deployment_info_id": str(arguments.deployment_info_id),
                "new_config_id": arguments.new_config_id,
            },
        )

    async def _commit(self, arguments: ToolArguments) -> JSONValue:
        assert isinstance(arguments, CommitArguments)
        return await self._request(
            "POST", "/api/action/commit", params={"message": arguments.message}
        )


__all__ = [
    "ThymisToolError",
    "ThymisTools",
    "ToolDefinition",
    "UnknownToolError",
]
