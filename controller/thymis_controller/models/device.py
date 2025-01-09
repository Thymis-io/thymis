from typing import Dict

from git import List
from pydantic import BaseModel, Field
from thymis_controller import db_models


class DeviceNotifyRequest(BaseModel):
    commit_hash: str | None
    config_id: str | None
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


class CreateHostkeyRequest(BaseModel):
    public_key: str
    device_host: str


__all__ = [
    "DeviceNotifyRequest",
    "Hostkey",
    "DeviceHeartbeatRequest",
    "CreateHostkeyRequest",
]
