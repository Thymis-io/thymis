from typing import Dict, Optional, Type
from app.nix import convert_python_value_to_nix
from pydantic import BaseModel


class Setting(BaseModel):
    name: str
    value: object = None
    type: str | object
    default: object
    description: str
    example: Optional[str] = None

    def get_value(self):
        if self.value is not None:
            return self.value
        else:
            return self.default

    def write_nix(self, f, priority):
        f.write(
            f"  {self.name} = lib.mkOverride {priority} {convert_python_value_to_nix(self.get_value())};\n"
        )


class SettingValue(BaseModel):
    value: object = None


class ModuleSettings(BaseModel):
    type: str  # type of module this settings object is for
    priority: int
    settings: Dict[str, SettingValue]
