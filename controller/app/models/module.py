import os
from typing import List, Optional
from typing_extensions import Unpack
from jinja2 import Environment
from pydantic import (
    BaseModel,
    SerializerFunctionWrapHandler,
    field_serializer,
    model_serializer,
)
from app import models
from pydoc import locate

from pydantic.config import ConfigDict


class Module(BaseModel):
    type: Optional[str] = None
    name: str

    def __init__(self, **data):
        # super().__init__(**data)
        # # also set name from classname if not set
        # if self.name is None:
        #     self.name = self.__class__.__name__.lower()

        # first set name then call super
        if "name" not in data:
            data["name"] = self.__class__.__name__.lower()
        if "type" not in data:
            data["type"] = f"{self.__class__.__module__}.{self.__class__.__name__}"
        super().__init__(**data)

    @classmethod
    def from_dict(cls, d):
        return locate(d["type"])(**d)

    @model_serializer(mode="wrap")
    def ser_model(self, nxt: SerializerFunctionWrapHandler):
        return nxt(self)

    def write_nix(
        self,
        path: os.PathLike,
        module_settings: models.ModuleSettings,
        priority: int,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+") as f:
            f.write("{ pkgs, lib, inputs, ... }:\n")
            f.write("{\n")

            self.write_nix_settings(f, module_settings, priority)

            f.write("}\n")

    def write_nix_settings(
        self, f, module_settings: models.ModuleSettings, priority: int
    ):
        for attr, value in module_settings.settings.items():
            my_attr = getattr(self, attr)
            assert isinstance(my_attr, models.Setting)
            my_attr.write_nix(f, value, priority)
