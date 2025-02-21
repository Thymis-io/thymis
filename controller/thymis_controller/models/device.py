import uuid
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field
from thymis_controller import db_models


class DeviceNotifyRequest(BaseModel):
    token: str | None = None
    hardware_ids: Dict[str, str | None]
    deployed_config_id: str
    public_key: str
    ip_addresses: List[str]


class DeviceHeartbeatRequest(BaseModel):
    public_key: str
    ip_addresses: List[str]


class Hostkey(BaseModel):
    identifier: str
    public_key: str
    device_host: str

    @staticmethod
    def from_deployment_info(deployment_info: db_models.DeploymentInfo) -> "Hostkey":
        return Hostkey(
            identifier=deployment_info.deployed_config_id,
            public_key=deployment_info.ssh_public_key,
            device_host=deployment_info.reachable_deployed_host,
        )


class CreateDeploymentInfoLegacyHostkeyRequest(BaseModel):
    deployed_config_id: str
    ssh_public_key: str
    reachable_deployed_host: str


class DeploymentInfo(BaseModel):
    id: uuid.UUID
    ssh_public_key: str | None
    deployed_config_commit: str | None
    deployed_config_id: str | None
    reachable_deployed_host: str | None
    last_seen: Optional[datetime]
    first_seen: Optional[datetime]
    hardware_devices: List["HardwareDevice"]

    @staticmethod
    def from_deployment_info(
        deployment_info: db_models.DeploymentInfo,
    ) -> "DeploymentInfo":
        return DeploymentInfo(
            id=deployment_info.id,
            ssh_public_key=deployment_info.ssh_public_key,
            deployed_config_commit=deployment_info.deployed_config_commit,
            deployed_config_id=deployment_info.deployed_config_id,
            reachable_deployed_host=deployment_info.reachable_deployed_host,
            hardware_devices=deployment_info.hardware_devices,
            last_seen=deployment_info.last_seen,
            first_seen=deployment_info.first_seen,
        )


class CreateHostkeyRequest(BaseModel):
    public_key: str
    device_host: str


class HardwareDevice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hardware_ids: Dict[str, str]
    deployment_info_id: uuid.UUID
    last_seen: Optional[datetime]


__all__ = [
    "DeviceNotifyRequest",
    "Hostkey",
    "DeviceHeartbeatRequest",
    "CreateHostkeyRequest",
    "DeploymentInfo",
    "CreateDeploymentInfoLegacyHostkeyRequest",
    "HardwareDevice",
]
