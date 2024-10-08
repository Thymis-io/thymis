from typing import List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field, JsonValue

type ValueTypes = Literal["bool", "string", "path", "package", "textarea", "int"]


class SelectOneType(BaseModel):
    select_one: List[Tuple[str, str]] = Field(serialization_alias="select-one")
    extra_data: Optional[dict[str, JsonValue]] = Field(default=None)


class ListType(BaseModel):
    settings: dict[str, "Setting"] = Field(serialization_alias="list-of")
    element_name: Optional[str] = Field(
        serialization_alias="element-name", default=None
    )


type SettingTypes = Union[ValueTypes, SelectOneType, ListType]


class Setting(BaseModel):
    displayName: str
    type: SettingTypes
    description: Optional[str] = None
    default: Optional[JsonValue] = None
    example: Optional[str] = None
    order: int = 0


class Module(BaseModel):
    type: str
    displayName: str
    icon: Optional[str] = None
    settings: dict[str, Setting]


__all__ = ["Setting", "Module", "SelectOneType", "ListType", "SettingTypes"]
