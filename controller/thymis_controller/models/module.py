import base64
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
from thymis_controller import models
from pydoc import locate

from pydantic.config import ConfigDict


class Module(BaseModel):
    type: Optional[str] = None
    name: str
    icon: Optional[str] = None

    def __init__(self, **data):
        # super().__init__(**data)
        # # also set name from classname if not set
        # if self.name is None:
        #     self.name = self.__class__.__name__.lower()

        # first set name then call super
        if "type" not in data:
            data["type"] = f"{self.__class__.__module__}.{self.__class__.__name__}"
        super().__init__(**data)

    @classmethod
    def from_dict(cls, d):
        # check if type starts with "app.". If so, replace with "thymis_controller."
        # print a warning message and a todo to implement versioning for the state
        if d["type"].startswith("app."):
            print(
                f"Warning: module type {d['type']} starts with old prefix 'app.'. Replacing with 'thymis_controller.'."
            )
            d["type"] = d["type"].replace("app.", "thymis_controller.")
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

    @staticmethod
    def read_into_base64(path: str):
        try:
            with open(path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
                extension = os.path.splitext(path)[1][1:]

                if extension == "svg":
                    extension = "svg+xml"

                return f"data:image/{extension};base64,{encoded}"
        except FileNotFoundError:
            print(f"File not found: {path}")
            return None
