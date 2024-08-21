from typing import List, Literal, Optional, Union

from pydantic import BaseModel

ValueTypes = Literal["bool", "string", "path", "package", "textarea"]


class SelectOneType(BaseModel):
    select_one: List[str]

    def __init__(self, select_one: List[str]):
        super().__init__(select_one=select_one)


class Setting(BaseModel):
    name: str
    type: Union[ValueTypes, SelectOneType]
    default: object
    description: str
    example: Optional[str] = None
    order: int = 0


class Module(BaseModel):
    type: str
    displayName: str
    icon: Optional[str] = None
    settings: dict[str, Setting]


__all__ = ["Setting", "Module", "SelectOneType"]
