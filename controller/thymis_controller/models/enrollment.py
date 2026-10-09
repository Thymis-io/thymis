import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EnrollRequest(BaseModel):
    code: str


class EnrollResponse(BaseModel):
    token: str


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


__all__ = ["EnrollRequest", "EnrollResponse", "PairingCode"]
