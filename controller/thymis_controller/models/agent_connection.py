import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from thymis_controller.models import DeploymentInfo


class AgentConnection(BaseModel):
    id: uuid.UUID
    connected_at: datetime
    disconnected_at: Optional[datetime]
    deployment_info: "DeploymentInfo"


__all__ = [
    "AgentConnection",
]
