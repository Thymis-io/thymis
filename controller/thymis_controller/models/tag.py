from typing import List
from pydantic import BaseModel
from thymis_controller import models


class Tag(BaseModel):
    displayName: str
    identifier: str
    priority: int
    modules: List[models.ModuleSettings]
