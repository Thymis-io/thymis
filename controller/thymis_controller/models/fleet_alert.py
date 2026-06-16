import uuid
from typing import Literal, Optional

from pydantic import BaseModel

AlertKind = Literal["offline", "flapping", "cpu", "ram", "disk"]
AlertSeverity = Literal["warning", "critical"]


class FleetAlert(BaseModel):
    deployment_info_id: uuid.UUID
    name: Optional[str] = None
    kind: AlertKind
    severity: AlertSeverity
    detail: str
    value: Optional[float] = None


__all__ = ["FleetAlert", "AlertKind", "AlertSeverity"]
