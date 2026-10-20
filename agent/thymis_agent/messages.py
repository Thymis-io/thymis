import datetime
import uuid
from typing import Any, Dict, List, Literal, Optional, Union

import http_network_relay.edge_agent as ea
from pydantic import BaseModel, Field


class AgentToRelayMessage(BaseModel):
    # This is a custom message that the agent sends to the relay
    inner: Union[
        "EtRSwitchToNewConfigResultMessage",
        "EtRMetricsMessage",
        "EtRNetworkInterfacesMessage",
    ] = Field(discriminator="kind")


class EtRSwitchToNewConfigResultMessage(BaseModel):
    kind: Literal["switch_to_new_config_result"] = "switch_to_new_config_result"
    task_id: uuid.UUID
    success: Optional[bool] = None  # in v3 dev
    error: Optional[str] = None  # in v3 dev
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
    network_interfaces: List[Dict[str, Any]]


class RelayToAgentMessage(BaseModel):
    # This is a custom message that the relay sends to the agent
    inner: Union[
        "RtEUpdatePublicKeyMessage",
        "RtESwitchToNewConfigMessage",
        "RtESuccesfullySSHConnectedMessage",
        "RtESendSecretsMessage",
        "RtEUpdateHostnameMessage",
    ] = Field(discriminator="kind")


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
    owner: Optional[str]
    group: Optional[str]
    mode: Optional[str]


class RtESendSecretsMessage(BaseModel):
    kind: Literal["send_secrets"] = "send_secrets"
    secrets: Dict[uuid.UUID, str]
    secret_infos: List[SecretForDevice]


class RtEUpdateHostnameMessage(BaseModel):
    kind: Literal["update_hostname"] = "update_hostname"
    hostname: str | None = None


class EdgeAgentToRelayStartMessage(ea.EtRStartMessage):
    token: str
    hardware_ids: Dict[str, str]
    public_key: str
    deployed_config_commit: Optional[str] = None
    deployed_config_id: Optional[str] = None
    ip_addresses: List[str] = []  # deprecated, used for backwards compatibility
    network_interfaces: List[Dict[str, Any]] = []
    ram_bytes: Optional[int] = None
    last_error: Optional[str] = None
