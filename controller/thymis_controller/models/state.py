import uuid
from typing import Dict, List, Optional

from pydantic import BaseModel, JsonValue
from thymis_controller import migration


class Repo(BaseModel):
    url: Optional[str] = None
    follows: Optional[str] = None
    inputs_follows: Dict[str, str] = {}
    api_key_secret: Optional[uuid.UUID] = None


class ModuleSettings(BaseModel):
    type: str  # type of module this settings object is for
    settings: Dict[str, JsonValue]


THYMIS_DEVICE_MODULE_TYPE = "thymis_controller.modules.thymis.ThymisDevice"


class Config(BaseModel):
    displayName: str
    identifier: str
    modules: List[ModuleSettings]
    tags: List[str]

    def device_type(self):
        for module in self.modules:
            if module.type == THYMIS_DEVICE_MODULE_TYPE:
                return module.settings.get("device_type")
        return None


class Tag(BaseModel):
    displayName: str
    identifier: str
    priority: int
    modules: List[ModuleSettings]


class State(BaseModel):
    version: str = migration.latest_version
    repositories: Dict[str, Repo] = {}
    tags: List[Tag] = []
    configs: List[Config] = []


__all__ = ["Repo", "ModuleSettings", "Config", "Tag", "State"]
