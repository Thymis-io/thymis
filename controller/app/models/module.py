from typing import List
from pydantic import BaseModel
from app import models


class Module(BaseModel):
    name: str
    enabled: models.Setting = models.Setting(
        name="enabled", type="bool", default=False, description="Whether the module is enabled", example="true"
    )

    def write_to_state():
        pass
