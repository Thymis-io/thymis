from pydantic import BaseModel


class RegisterDeviceRequest(BaseModel):
    build_hash: str
    public_key: str


__all__ = ["RegisterDeviceRequest"]
