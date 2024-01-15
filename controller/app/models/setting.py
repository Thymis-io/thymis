from typing import Dict, Optional, Type
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

class SettingValue(BaseModel):
    value: object = None


class ModuleSettings(BaseModel):
    type: str
    settings: Dict[str, SettingValue]
