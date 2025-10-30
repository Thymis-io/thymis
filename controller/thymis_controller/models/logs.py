import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_serializer
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

    @field_serializer("timestamp")
    def _ser_dt(self, dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            # treat stored naive values as UTC
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")

    @staticmethod
    def from_db_model(log_entry: db_models.LogEntry) -> "LogEntry":
        return LogEntry(
            uuid=log_entry.id,
            timestamp=log_entry.timestamp,
            message=log_entry.message,
            host=log_entry.hostname,
            facility=log_entry.facility,
            severity=log_entry.severity,
            programname=log_entry.programname,
            syslogtag=log_entry.syslogtag,
        )


class LogList(BaseModel):
    total_count: int
    logs: list[LogEntry]
