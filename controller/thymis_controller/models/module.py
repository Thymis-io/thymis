from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

ValueTypes = Literal["bool", "string", "path", "package", "textarea"]


class SelectOneType(BaseModel):
    select_one: List[str] = Field(serialization_alias="select-one")


Types = Union[ValueTypes, SelectOneType]


class Setting(BaseModel):
    name: str
    type: Types
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
