# Got logs data: b'{"message":" Connection closed with error: received 1012 (service restart); then sent 1012 (service restart)","facility":3,"severity":6,"syslogtag":"thymis-agent-start[3149]:","programname":"thymis-agent-start","host":"asdasd","timestamp":"2025-04-29T15:47:30.895708+02:00","uuid":"7910600A94F24FE4B7A1D05AABDFFFBF"}'

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
