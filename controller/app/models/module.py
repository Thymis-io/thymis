from typing import List
from pydantic import BaseModel
from app import models


class Module(BaseModel):
    name: str

    enable: models.Setting = models.Setting(
        name="enable", type="bool", default=False, description="Whether the module is enable", example="true"
    )
