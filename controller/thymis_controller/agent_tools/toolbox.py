"""HTTP-backed, provider-neutral tools for agents that manage Thymis."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from typing import Any

import httpx

from .arguments import (
    ArtifactArguments,
    BuildImageArguments,
    CommitArguments,
    CreateSecretArguments,
    DeployArguments,
    DeploymentInfoArguments,
    DeviceMetricsArguments,
    DiffArguments,
    EmptyArguments,
    ExternalRepositoryArguments,
    FleetRangeArguments,
    ListTasksArguments,
    LogArguments,
    RenameArtifactArguments,
    RestartDeviceArguments,
    RunDeviceCommandArguments,
    SecretArguments,
    SwitchConfigArguments,
    TaskArguments,
    UpdateControllerSettingsArguments,
    UpdateDeploymentInfoArguments,
    UpdateSecretArguments,
    UpdateStateArguments,
    UploadArtifactsArguments,
)
from .registry import (
    JSONValue,
    ToolArguments,
    ToolDefinition,
    UnknownToolError,
    collect_tools,
    tool,
)


class ThymisToolError(RuntimeError):
    """An API failure with enough context for an agent to recover safely."""

    def __init__(self, status_code: int, method: str, path: str, detail: Any):
        self.status_code = status_code
        self.method = method
        self.path = path
        self.detail = detail
        super().__init__(f"{method} {path} failed with {status_code}: {detail}")


class ThymisTools:
    """Typed operations available to an authenticated Thymis agent.

    The caller owns the supplied ``httpx.AsyncClient`` and its authentication
    cookies. Agent authorization and validation therefore remain identical to
    the browser's existing controller API boundary.
    """

    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._tools = collect_tools(self)

    def definitions(self) -> list[ToolDefinition]:
        """Return the complete tool catalogue for an agent runtime."""
        return [tool.definition() for tool in self._tools.values()]

    async def invoke(
        self, name: str, arguments: Mapping[str, Any] | None = None
    ) -> JSONValue:
        """Validate and execute one named tool call."""
        try:
            registered_tool = self._tools[name]
        except KeyError as error:
            raise UnknownToolError(f"Unknown Thymis tool: {name}") from error
        return await registered_tool.invoke(arguments)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Any = None,
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

    # Configuration ---------------------------------------------------------

    @tool(
        EmptyArguments,
        "Read the complete Thymis configuration state, including configurations, tags, and repositories.",
    )
    async def get_state(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/state")

    @tool(
        UpdateStateArguments,
        "Replace the complete Thymis configuration state. Read the state first, preserve unrelated fields, then commit before deployment.",
    )
    async def update_state(self, arguments: UpdateStateArguments) -> JSONValue:
        return await self._request(
            "PATCH", "/api/state", json=arguments.state.model_dump(mode="json")
        )

    @tool(
        EmptyArguments,
        "List all available NixOS module definitions and their configurable settings.",
    )
    async def list_available_modules(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/available_modules")

    # Devices and live telemetry -------------------------------------------

    @tool(
        EmptyArguments,
        "List every registered device with connection, deployment, and metadata state.",
    )
    async def list_deployment_infos(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/all_deployment_infos")

    @tool(DeploymentInfoArguments, "Get one registered device by deployment-info ID.")
    async def get_deployment_info(
        self, arguments: DeploymentInfoArguments
    ) -> JSONValue:
        return await self._request(
            "GET", f"/api/deployment_info/{arguments.deployment_info_id}"
        )

    @tool(
        UpdateDeploymentInfoArguments,
        "Update device metadata such as name, location, notes, archive status, or configured host details.",
    )
    async def update_deployment_info(
        self, arguments: UpdateDeploymentInfoArguments
    ) -> JSONValue:
        return await self._request(
            "PATCH",
            f"/api/deployment_info/{arguments.deployment_info_id}",
            json=arguments.changes.model_dump(exclude_unset=True, mode="json"),
        )

    @tool(
        DeploymentInfoArguments,
        "Permanently remove a registered device from the controller.",
        name="delete_deployment_info",
    )
    async def delete_deployment_info(
        self, arguments: DeploymentInfoArguments
    ) -> JSONValue:
        return await self._request(
            "DELETE", f"/api/deployment_info/{arguments.deployment_info_id}"
        )

    @tool(EmptyArguments, "List known device hardware records.")
    async def list_hardware_devices(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/hardware_device")

    @tool(
        DeploymentInfoArguments,
        "Read a device's recent controller connection history.",
    )
    async def get_device_connection_history(
        self, arguments: DeploymentInfoArguments
    ) -> JSONValue:
        return await self._request(
            "GET",
            f"/api/deployment_info/{arguments.deployment_info_id}/connection_history",
        )

    @tool(
        DeviceMetricsArguments,
        "Read downsampled CPU, RAM, and disk metrics for one device.",
    )
    async def get_device_metrics(self, arguments: DeviceMetricsArguments) -> JSONValue:
        return await self._request(
            "GET",
            f"/api/deployment_info/{arguments.deployment_info_id}/metrics",
            params={
                "hours": arguments.hours,
                "granularity": arguments.granularity.value,
            },
        )

    @tool(
        DeploymentInfoArguments,
        "Read the 50 most recent Error and Critical log entries for one device.",
    )
    async def get_device_error_logs(
        self, arguments: DeploymentInfoArguments
    ) -> JSONValue:
        return await self._request(
            "GET", f"/api/deployment_info/{arguments.deployment_info_id}/error_logs"
        )

    @tool(
        RunDeviceCommandArguments,
        "Run one shell command as root on a connected device. The command runs asynchronously; use get_task with the returned task_id to inspect completion and output.",
    )
    async def run_device_command(
        self, arguments: RunDeviceCommandArguments
    ) -> JSONValue:
        return await self._request(
            "POST",
            "/api/action/run-command",
            params={
                "deployment_info_id": str(arguments.deployment_info_id),
                "command": arguments.command,
            },
        )

    # Background tasks ------------------------------------------------------

    @tool(
        ListTasksArguments,
        "List background build, deployment, and device-command tasks.",
    )
    async def list_tasks(self, arguments: ListTasksArguments) -> JSONValue:
        return await self._request(
            "GET",
            "/api/tasks",
            params={"limit": arguments.limit, "offset": arguments.offset},
        )

    @tool(TaskArguments, "Get detailed status and output for one background task.")
    async def get_task(self, arguments: TaskArguments) -> JSONValue:
        return await self._request("GET", f"/api/tasks/{arguments.task_id}")

    @tool(TaskArguments, "Cancel one pending or running background task.")
    async def cancel_task(self, arguments: TaskArguments) -> JSONValue:
        return await self._request("POST", f"/api/tasks/{arguments.task_id}/cancel")

    @tool(TaskArguments, "Retry a failed background task.")
    async def retry_task(self, arguments: TaskArguments) -> JSONValue:
        return await self._request("POST", f"/api/tasks/{arguments.task_id}/retry")

    # Secrets and artifacts -------------------------------------------------

    @tool(
        EmptyArguments,
        "List configured secrets. Responses follow the authenticated controller API and may contain non-file secret text.",
    )
    async def list_secrets(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/secrets")

    @tool(
        CreateSecretArguments,
        "Create a secret. Supply either value_str or value_b64 in the nested secret payload.",
    )
    async def create_secret(self, arguments: CreateSecretArguments) -> JSONValue:
        return await self._request(
            "POST", "/api/secrets", json=arguments.secret.model_dump(mode="json")
        )

    @tool(
        UpdateSecretArguments,
        "Update secret metadata or value. Only explicitly supplied nested fields are sent.",
    )
    async def update_secret(self, arguments: UpdateSecretArguments) -> JSONValue:
        return await self._request(
            "PATCH",
            f"/api/secrets/{arguments.secret_id}",
            json=arguments.changes.model_dump(exclude_unset=True, mode="json"),
        )

    @tool(SecretArguments, "Permanently delete one secret.", name="delete_secret")
    async def delete_secret(self, arguments: SecretArguments) -> JSONValue:
        return await self._request("DELETE", f"/api/secrets/{arguments.secret_id}")

    @tool(EmptyArguments, "List uploaded configuration artifacts.")
    async def list_artifacts(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/artifacts")

    @tool(
        UploadArtifactsArguments,
        "Upload one or more base64-encoded artifacts for configuration modules to reference.",
    )
    async def upload_artifacts(self, arguments: UploadArtifactsArguments) -> JSONValue:
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

    @tool(
        RenameArtifactArguments,
        "Rename an artifact and update state references to its old name.",
    )
    async def rename_artifact(self, arguments: RenameArtifactArguments) -> JSONValue:
        return await self._request(
            "POST",
            f"/api/artifacts/rename/{arguments.name}",
            params={"new_name": arguments.new_name},
        )

    @tool(ArtifactArguments, "Permanently delete one artifact.", name="delete_artifact")
    async def delete_artifact(self, arguments: ArtifactArguments) -> JSONValue:
        return await self._request("DELETE", f"/api/artifacts/{arguments.name}")

    # Repository and controller state --------------------------------------

    @tool(EmptyArguments, "Read the configuration repository commit history.")
    async def get_history(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/history")

    @tool(DiffArguments, "Read the repository diff between two optional revisions.")
    async def get_history_diff(self, arguments: DiffArguments) -> JSONValue:
        params = {
            key: value
            for key, value in (("refA", arguments.ref_a), ("refB", arguments.ref_b))
            if value is not None
        }
        return await self._request("GET", "/api/history/diff", params=params)

    @tool(EmptyArguments, "Read uncommitted configuration repository changes.")
    async def get_repo_status(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/repo_status")

    @tool(
        LogArguments,
        "Query structured device logs with optional time and program filters.",
        name="get_logs",
    )
    async def get_logs(self, arguments: LogArguments) -> JSONValue:
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

    @tool(
        DeploymentInfoArguments,
        "List program names present in a device's logs.",
        name="list_log_program_names",
    )
    async def list_log_program_names(
        self, arguments: DeploymentInfoArguments
    ) -> JSONValue:
        return await self._request(
            "GET", f"/api/logs/{arguments.deployment_info_id}/program-names"
        )

    @tool(
        FleetRangeArguments,
        "Get fleet connectivity time series for a bounded time range.",
        name="get_fleet_connectivity",
    )
    async def get_fleet_connectivity(self, arguments: FleetRangeArguments) -> JSONValue:
        return await self._request(
            "GET",
            "/api/fleet/connectivity",
            params={"hours": arguments.hours, "buckets": arguments.buckets},
        )

    @tool(EmptyArguments, "Get the latest resource metrics for every reporting device.")
    async def get_fleet_metrics_latest(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/fleet/metrics/latest")

    @tool(
        FleetRangeArguments,
        "Get fleet availability buckets for a bounded time range.",
        name="get_fleet_availability",
    )
    async def get_fleet_availability(self, arguments: FleetRangeArguments) -> JSONValue:
        return await self._request(
            "GET",
            "/api/fleet/availability",
            params={"hours": arguments.hours, "buckets": arguments.buckets},
        )

    @tool(EmptyArguments, "List active fleet alerts.")
    async def get_fleet_alerts(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/fleet/alerts")

    @tool(EmptyArguments, "Read automatic update settings and schedule.")
    async def get_controller_settings(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/controller-settings")

    @tool(
        UpdateControllerSettingsArguments,
        "Update automatic update enablement and/or schedule.",
        name="update_controller_settings",
    )
    async def update_controller_settings(
        self, arguments: UpdateControllerSettingsArguments
    ) -> JSONValue:
        return await self._request(
            "PATCH",
            "/api/controller-settings",
            json=arguments.model_dump(exclude_unset=True, mode="json"),
        )

    @tool(
        EmptyArguments,
        "Read synchronization status for configured external flake repositories.",
        name="get_external_repository_status",
    )
    async def get_external_repository_status(self, _: EmptyArguments) -> JSONValue:
        return await self._request("GET", "/api/external-repositories/status")

    @tool(
        ExternalRepositoryArguments,
        "Parse and return the flake reference for one configured external repository.",
        name="get_external_repository_flake_ref",
    )
    async def get_external_repository_flake_ref(
        self, arguments: ExternalRepositoryArguments
    ) -> JSONValue:
        return await self._request(
            "GET", f"/api/external-repositories/flake-ref/{arguments.flake_name}"
        )

    # Build and deployment actions -----------------------------------------

    @tool(
        EmptyArguments,
        "Queue a build of the current configuration project.",
        name="build_project",
    )
    async def build_project(self, _: EmptyArguments) -> JSONValue:
        return await self._request("POST", "/api/action/build")

    @tool(
        DeployArguments,
        "Queue deployment of selected configurations and/or devices. The repository must be clean and selected devices must be connected.",
    )
    async def deploy(self, arguments: DeployArguments) -> JSONValue:
        params = [("config", identifier) for identifier in arguments.config_identifiers]
        params.extend(
            ("deployment_info_id", str(deployment_info_id))
            for deployment_info_id in arguments.deployment_info_ids
        )
        return await self._request("POST", "/api/action/deploy", params=params)

    @tool(
        BuildImageArguments,
        "Queue a bootable image build for one configuration. The repository must be clean.",
        name="build_device_image",
    )
    async def build_device_image(self, arguments: BuildImageArguments) -> JSONValue:
        return await self._request(
            "POST",
            "/api/action/build-download-image",
            params={"identifier": arguments.identifier},
        )

    @tool(
        RestartDeviceArguments,
        "Queue a reboot for connected devices using one configuration identifier.",
        name="restart_device",
    )
    async def restart_device(self, arguments: RestartDeviceArguments) -> JSONValue:
        return await self._request(
            "POST",
            "/api/action/restart-device",
            params={"identifier": arguments.identifier},
        )

    @tool(
        SwitchConfigArguments,
        "Switch a connected device to a compatible configuration and deploy it immediately. The repository must be clean.",
        name="switch_device_config",
    )
    async def switch_device_config(self, arguments: SwitchConfigArguments) -> JSONValue:
        return await self._request(
            "POST",
            "/api/action/switch-config",
            params={
                "deployment_info_id": str(arguments.deployment_info_id),
                "new_config_id": arguments.new_config_id,
            },
        )

    @tool(
        CommitArguments,
        "Commit current configuration repository changes with a message.",
    )
    async def commit(self, arguments: CommitArguments) -> JSONValue:
        return await self._request(
            "POST", "/api/action/commit", params={"message": arguments.message}
        )

    @tool(
        EmptyArguments,
        "Queue an update of project flake inputs.",
        name="update_project",
    )
    async def update_project(self, _: EmptyArguments) -> JSONValue:
        return await self._request("POST", "/api/action/update")

    @tool(
        EmptyArguments,
        "Queue the controller's automatic update workflow for connected devices.",
        name="auto_update",
    )
    async def auto_update(self, _: EmptyArguments) -> JSONValue:
        return await self._request("POST", "/api/action/auto-update")
