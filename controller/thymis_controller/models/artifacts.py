import datetime

from pydantic import BaseModel


class Artifact(BaseModel):
    name: str
    media_type: str | None = None
    size: int
    created_at: datetime.datetime
    modified_at: datetime.datetime
