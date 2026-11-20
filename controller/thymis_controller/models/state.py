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
    # Per-setting priority overrides, keyed by setting name. The value is used
    # as the lib.mkOverride priority for the nix definitions emitted for that
    # setting (lowest number wins in the NixOS module system). Settings without
    # an entry use the priority of the tag/config this object belongs to.
    priorities: Dict[str, int] = {}

    def setting_priority(self, setting_key: str, default: int) -> int:
        """Priority to emit this setting with, defaulting to the owning
        tag/config priority when the setting has no override."""
        return self.priorities.get(setting_key, default)


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
