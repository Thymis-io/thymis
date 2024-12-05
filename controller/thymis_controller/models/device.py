from git import List
from pydantic import BaseModel, Field


class RegisterDeviceRequest(BaseModel):
    build_hash: str
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
    "RegisterDeviceRequest",
    "Hostkey",
    "DeviceHeartbeatRequest",
    "CreateHostkeyRequest",
]
