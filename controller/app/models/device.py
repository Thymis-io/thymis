from typing import List
from pydantic import BaseModel
from app import models


class Device(BaseModel):
    hostname: str
    displayName: str
    modules: List[models.ModuleSettings]
    tags: List[str]
