"""Messages exchanged between the agent and the controller's relay.

`EtR*` messages go from the edge agent to the relay, `RtE*` the other way.
"""

import datetime
import uuid
from typing import Any, Literal

import http_network_relay.edge_agent as ea
from pydantic import BaseModel, Field


class EdgeAgentToRelayStartMessage(ea.EtRStartMessage):
    token: str
    hardware_ids: dict[str, str]
    public_key: str
    deployed_config_commit: str | None = None
    deployed_config_id: str | None = None
    ip_addresses: list[str] = []  # deprecated, used for backwards compatibility
    network_interfaces: list[dict[str, Any]] = []
    ram_bytes: int | None = None
    last_error: str | None = None


class EtRSwitchToNewConfigResultMessage(BaseModel):
    kind: Literal["switch_to_new_config_result"] = "switch_to_new_config_result"
    task_id: uuid.UUID
    success: bool | None = None  # in v3 dev
    error: str | None = None  # in v3 dev
    configuration_id: str | None = None  # v3 final
    config_commit: str | None = None  # in v3 final
    is_activated: bool | None = None  # in v3 final
    switch_success: bool | None = None  # in v3 final
    stdout: str | None = None  # in v3 final
    stderr: str | None = None  # in v3 final
    # the switch was activated but units failed to reload/restart, so a reboot
    # is needed before the update is fully in effect
    reboot_required: bool | None = None


class EtRMetricsMessage(BaseModel):
    kind: Literal["metrics"] = "metrics"
    timestamp: datetime.datetime
    cpu_percent: float
    ram_percent: float
    disk_percent: float


class EtRNetworkInterfacesMessage(BaseModel):
    kind: Literal["network_interfaces"] = "network_interfaces"
    network_interfaces: list[dict[str, Any]]


class AgentToRelayMessage(BaseModel):
    inner: (
        EtRSwitchToNewConfigResultMessage
        | EtRMetricsMessage
        | EtRNetworkInterfacesMessage
    ) = Field(discriminator="kind")


class RtEUpdatePublicKeyMessage(BaseModel):
    kind: Literal["update_public_key"] = "update_public_key"


class RtESwitchToNewConfigMessage(BaseModel):
    kind: Literal["switch_to_new_config"] = "switch_to_new_config"
    new_path_to_config: str
    configuration_id: str
    config_commit: str
    task_id: uuid.UUID


class RtESuccesfullySSHConnectedMessage(BaseModel):
    kind: Literal["successfully_ssh_connected"] = "successfully_ssh_connected"


class SecretForDevice(BaseModel):
    secret_id: uuid.UUID
    path: str
    owner: str | None
    group: str | None
    mode: str | None


class RtESendSecretsMessage(BaseModel):
    kind: Literal["send_secrets"] = "send_secrets"
    secrets: dict[uuid.UUID, str]
    secret_infos: list[SecretForDevice]


class RtEUpdateHostnameMessage(BaseModel):
    kind: Literal["update_hostname"] = "update_hostname"
    hostname: str | None = None


class RelayToAgentMessage(BaseModel):
    inner: (
        RtEUpdatePublicKeyMessage
        | RtESwitchToNewConfigMessage
        | RtESuccesfullySSHConnectedMessage
        | RtESendSecretsMessage
        | RtEUpdateHostnameMessage
    ) = Field(discriminator="kind")
