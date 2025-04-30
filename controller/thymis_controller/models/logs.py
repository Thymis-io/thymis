import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from thymis_controller import db_models


class LogEntry(BaseModel):
    uuid: uuid.UUID
    timestamp: datetime
    message: str
    host: str
    facility: int
    severity: int
    programname: str
    syslogtag: str
