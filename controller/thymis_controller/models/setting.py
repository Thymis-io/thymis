from typing import Dict, Optional, Type
from thymis_controller.nix import convert_python_value_to_nix
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

    def __init__(self, **data):
        if data["type"].startswith("app."):
            print(
                f"Warning: module type {data['type']} starts with old prefix 'app.'. Replacing with 'thymis_controller.'."
            )
            data["type"] = data["type"].replace("app.", "thymis_controller.")
        super().__init__(**data)
