from typing import List
from pydantic import BaseModel
from thymis_controller import models


class Device(BaseModel):
    hostname: str
    displayName: str
    modules: List[models.ModuleSettings]
    tags: List[str]
