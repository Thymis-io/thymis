import uuid
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, JsonValue, field_validator
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


class ConfigFieldPatch(BaseModel):
    """One RFC 6901 JSON Pointer mutation scoped to a configuration."""

    operation: Literal["set", "remove"] = "set"
    path: str
    value: JsonValue | None = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, path: str) -> str:
        if not path.startswith("/"):
            raise ValueError("path must be a non-empty JSON Pointer starting with '/'")
        if path == "/identifier":
            raise ValueError(
                "configuration identifier cannot be changed by a field patch"
            )
        return path


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


__all__ = ["Repo", "ModuleSettings", "Config", "ConfigFieldPatch", "Tag", "State"]
