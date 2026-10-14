import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class EnrollRequest(BaseModel):
    code: str
    nonce: str


class EnrollResponse(BaseModel):
    token: str
    controller_ssh_pubkey: Optional[str] = None


class ControllerPublicKeyResponse(BaseModel):
    controller_ssh_pubkey: Optional[str] = None


class PairingCode(BaseModel):
    """Omits the token it resolves to: that only leaves the controller
    through `POST /agent/enroll`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    revoked: bool
    created_at: datetime
    expires_at: datetime
    redeemed_at: Optional[datetime]

    @field_serializer("created_at", "expires_at", "redeemed_at")
    def _ser_dt(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            # treat stored naive values as UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")


class PairingCodeList(BaseModel):
    """`recent` holds codes from the last days that can no longer be redeemed."""

    active: list[PairingCode]
    recent: list[PairingCode]


__all__ = [
    "ControllerPublicKeyResponse",
    "EnrollRequest",
    "EnrollResponse",
    "PairingCode",
    "PairingCodeList",
]
