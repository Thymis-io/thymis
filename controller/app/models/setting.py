from typing import Dict, Optional, Type
from app.nix import convert_python_value_to_nix
from pydantic import BaseModel


class Setting(BaseModel):
    name: str
    type: str | object
    default: object
    description: str
    example: Optional[str] = None

    def write_nix(self, f, value, priority):
        f.write(
            f"  {self.name} = lib.mkOverride {priority} {convert_python_value_to_nix(value.value)};\n"
        )


class SettingValue(BaseModel):
    value: object = None


class ModuleSettings(BaseModel):
    type: str  # type of module this settings object is for
    settings: Dict[str, SettingValue]
