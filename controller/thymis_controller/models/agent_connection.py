import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, field_serializer

if TYPE_CHECKING:
    from thymis_controller.models import DeploymentInfo


class AgentConnection(BaseModel):
    id: uuid.UUID
    connected_at: datetime
    disconnected_at: Optional[datetime]
    deployment_info: "DeploymentInfo"


class AgentConnectionShort(BaseModel):
    id: uuid.UUID
    connected_at: datetime
    disconnected_at: Optional[datetime]


class ConnectivityPoint(BaseModel):
    timestamp: datetime
    connected_count: int

    @field_serializer("timestamp")
    def _ser_dt(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")


__all__ = [
    "AgentConnection",
    "AgentConnectionShort",
    "ConnectivityPoint",
]
