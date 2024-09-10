from git import List
from pydantic import BaseModel


class RegisterDeviceRequest(BaseModel):
    build_hash: str
    public_key: str
    ip_addresses: List[str]


class RegisteredDevice(BaseModel):
    identifier: str
    public_key: str
    device_host: str


__all__ = ["RegisterDeviceRequest", "RegisteredDevice"]
