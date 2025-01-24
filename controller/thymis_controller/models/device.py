import uuid
from typing import Dict

from git import List
from pydantic import BaseModel, ConfigDict, Field
from thymis_controller import db_models


class DeviceNotifyRequest(BaseModel):
    token: str | None = None
    hardware_ids: Dict[str, str | None]
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
        )


class CreateHostkeyRequest(BaseModel):
    public_key: str
    device_host: str


class HardwareDevice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hardware_ids: Dict[str, str]
    deployment_info: DeploymentInfo


__all__ = [
    "DeviceNotifyRequest",
    "Hostkey",
    "DeviceHeartbeatRequest",
    "CreateHostkeyRequest",
    "DeploymentInfo",
    "CreateDeploymentInfoLegacyHostkeyRequest",
    "HardwareDevice",
]
