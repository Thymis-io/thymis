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
    identifier: str = Field(serialization_alias="identifier")
    public_key: str = Field(serialization_alias="publicKey")
    device_host: str = Field(serialization_alias="deviceHost")


class CreateHostkeyRequest(BaseModel):
    public_key: str = Field(serialization_alias="publicKey")
    device_host: str = Field(serialization_alias="deviceHost")


__all__ = [
    "RegisterDeviceRequest",
    "Hostkey",
    "DeviceHeartbeatRequest",
    "CreateHostkeyRequest",
]
