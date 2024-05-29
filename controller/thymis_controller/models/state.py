from typing import Dict, List, Optional

from pydantic import BaseModel
from thymis_controller import migration


class Repo(BaseModel):
    url: Optional[str] = None
    follows: Optional[str] = None
    inputs_follows: Dict[str, str] = {}


class ModuleSettings(BaseModel):
    type: str  # type of module this settings object is for
    settings: Dict[str, str | int | float | bool]


class Device(BaseModel):
    displayName: str
    identifier: str
    targetHost: str
    modules: List[ModuleSettings]
    tags: List[str]


class Tag(BaseModel):
    displayName: str
    identifier: str
    priority: int
    modules: List[ModuleSettings]


class State(BaseModel):
    version: str = migration.latest_version
    repositories: Dict[str, Repo]
    tags: List[Tag]
    devices: List[Device]


__all__ = ["Repo", "ModuleSettings", "Device", "Tag", "State"]
