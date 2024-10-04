import datetime
from typing import List

from pydantic import BaseModel


class Commit(BaseModel):
    SHA: str
    SHA1: str
    message: str
    date: datetime.datetime
    author: str
    state_diff: List[str]


class Remote(BaseModel):
    name: str
    url: str


__all__ = ["Commit", "Remote"]
