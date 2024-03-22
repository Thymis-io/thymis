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

    @classmethod
    def from_dict(cls, d):
        # check if type starts with "app.". If so, replace with "thymis_controller."
        # print a warning message and a todo to implement versioning for the state
        if d["type"].startswith("app."):
            print(
                f"Warning: module type {d['type']} starts with old prefix 'app.'. Replacing with 'thymis_controller.'."
            )
            d["type"] = d["type"].replace("app.", "thymis_controller.")
        return cls(**d)
