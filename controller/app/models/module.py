from typing import List, Optional
from pydantic import BaseModel
from app import models


class Module(BaseModel):
    type: Optional[str] = None
    name: str

    enable: models.Setting = models.Setting(
        name="enable", type="bool", default=False, description="Whether the module is enable", example="true"
    )
