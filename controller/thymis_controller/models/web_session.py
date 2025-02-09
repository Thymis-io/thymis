import datetime
import uuid

from pydantic import BaseModel


class WebSession(BaseModel):
    id: int
    session_id: uuid.UUID
    created_at: datetime.datetime


__all__ = ["WebSession"]
