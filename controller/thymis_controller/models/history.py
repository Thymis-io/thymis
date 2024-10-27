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
    branches: list[str]


class GitInfo(BaseModel):
    active_branch: str
    remote_branch: str | None
    ahead: int
    behind: int
    remotes: List[Remote]


__all__ = ["Commit", "Remote", "GitInfo"]
