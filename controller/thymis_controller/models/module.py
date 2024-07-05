from typing import List, Literal, Optional

from pydantic import BaseModel


class Setting(BaseModel):
    name: str
    type: Literal["bool", "string", "path", "package", "select-one", "textarea"]
    options: Optional[List[str]] = None
    default: object
    description: str
    example: Optional[str] = None
    order: int = 0


class Module(BaseModel):
    type: str
    displayName: str
    icon: Optional[str] = None
    settings: dict[str, Setting]


__all__ = ["Setting", "Module"]
