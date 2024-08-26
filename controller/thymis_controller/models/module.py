from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field

ValueTypes = Literal["bool", "string", "path", "package", "textarea"]


class SelectOneType(BaseModel):
    select_one: List[str] = Field(serialization_alias="select-one")


class ListType(BaseModel):
    settings: dict[str, "Setting"] = Field(serialization_alias="list-of")
    element_name: Optional[str] = Field(
        serialization_alias="element-name", default=None
    )


Types = Union[ValueTypes, SelectOneType, ListType]


class Setting(BaseModel):
    name: Optional[str] = None
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


__all__ = ["Setting", "Module", "SelectOneType", "ListType"]
