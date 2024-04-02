from typing import List
from pydantic import BaseModel
from thymis_controller import models


class Device(BaseModel):
    displayName: str
    identifier: str
    targetHost: str
    modules: List[models.ModuleSettings]
    tags: List[str]
