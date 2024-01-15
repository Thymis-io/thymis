
from typing import List
from pydantic import BaseModel
from app import models


class Tag(BaseModel):
    name: str
    priority: int
    modules: List[models.ModuleSettings]
