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


def convert_python_value_to_nix(value):
    if isinstance(value, bool):
        return str(value).lower()
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, list):
        return f"[{' '.join([convert_python_value_to_nix(v) for v in value])}]"
    else:
        return str(value)


class Module(BaseModel):
    type: Optional[str] = None
    name: str

    enable: models.Setting = models.Setting(
        name="enable",
        type="bool",
        default=False,
        description="Whether the module is enable",
        example="true",
    )

    def __init__(self, **data):
        # super().__init__(**data)
        # # also set name from classname if not set
        # if self.name is None:
        #     self.name = self.__class__.__name__.lower()

        # first set name then call super
        if "name" not in data:
            data["name"] = self.__class__.__name__.lower()
        super().__init__(**data)

    def write_nix(self, path: os.PathLike, env: Environment):
        # filename = f"{self.name}.nix"
        # use classname, but first letter lowercase
        classname = self.__class__.__name__
        filename = f"{classname[0].lower()}{classname[1:]}.nix"

        with open(path / filename, "w+") as f:
            f.write("{ pkgs, lib, ... }:\n")
            f.write("{\n")
            # for attr in dir(self):
            # use model_fields_set
            for attr in self.model_fields_set:
                attr = getattr(self, attr)
                if isinstance(attr, models.Setting):
                    f.write(
                        f"  {attr.name} = {convert_python_value_to_nix(attr.get_value())};\n"
                    )
            f.write("}\n")

    @classmethod
    def from_dict(cls, d):
        return locate(d["type"])(**d)

    @model_serializer(mode="wrap")
    def ser_model(self, nxt: SerializerFunctionWrapHandler):
        d = nxt(self)
        d["type"] = f"{self.__class__.__module__}.{self.__class__.__name__}"
        return d
