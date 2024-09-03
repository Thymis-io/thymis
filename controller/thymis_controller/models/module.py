from typing import List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field

ValueTypes = Literal["bool", "string", "path", "package", "textarea", "int"]


class SelectOneType(BaseModel):
    select_one: List[Tuple[str, str]] = Field(serialization_alias="select-one")

    def localize(self, locales: dict):
        self.select_one = [
            (key, locales.get(value, value)) for (key, value) in self.select_one
        ]


class ListType(BaseModel):
    settings: dict[str, "Setting"] = Field(serialization_alias="list-of")
    element_name: Optional[str] = Field(
        serialization_alias="element-name", default=None
    )

    def localize(self, locales: dict):
        for key, value in self.settings.items():
            value.localize(locales)
        self.element_name = locales.get(self.element_name, self.element_name)


Types = Union[ValueTypes, SelectOneType, ListType]


class Setting(BaseModel):
    name: Optional[str] = None
    type: Types
    default: object
    description: str
    example: Optional[str] = None
    order: int = 0

    def localize(self, locales: dict):
        self.name = locales.get(self.name, self.name)
        self.description = locales.get(self.description, self.description)

        if isinstance(self.type, (ListType, SelectOneType)):
            self.type.localize(locales)


class Module(BaseModel):
    type: str
    displayName: str
    icon: Optional[str] = None
    settings: dict[str, Setting]


__all__ = ["Setting", "Module", "SelectOneType", "ListType"]
