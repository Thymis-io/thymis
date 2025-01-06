from typing import Dict

from git import List
from pydantic import BaseModel, Field


class DeviceNotifyRequest(BaseModel):
    commit_hash: str | None
    config_id: str
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


class CreateHostkeyRequest(BaseModel):
    public_key: str
    device_host: str


__all__ = [
    "DeviceNotifyRequest",
    "Hostkey",
    "DeviceHeartbeatRequest",
    "CreateHostkeyRequest",
]
