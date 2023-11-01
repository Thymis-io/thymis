from typing import Type
from pydantic import BaseModel


class Setting(BaseModel):
    name: str
    type: str
    default: object
    description: str
    example: str
