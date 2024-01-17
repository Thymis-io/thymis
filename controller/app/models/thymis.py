import json
import os
from jinja2 import Environment
from . import Module, Setting
import pathlib

from app import models


class Thymis(Module):
    repo_dir: Setting = Setting(
        name="repo-dir",
        type="string",
        default="/var/lib/thymis",
        description="The directory where the thymis repository is located.",
        example="/var/lib/thymis",
    )
    device_type: Setting = Setting(
        name="device-type",
        type="string",
        default="",
        description="The device type of the thymis device.",
        example="",
    )
    device_name: Setting = Setting(
        name="device-name",
        type="string",
        default="",
        description="The device name of the thymis device.",
        example="",
    )
    password: Setting = Setting(
        name="password",
        type="string",
        default="",
        description="The password of the thymis device.",
        example="",
    )

    def write_nix(self, path: os.PathLike, module_settings: models.ModuleSettings, priority: int):
        # return super().write_nix(path, env)
        path = pathlib.Path(path)
        with open(path / ".." / "thymis-settings.json", "w+") as f:
            d = {}
            for attr in self.model_fields_set:
                attr = getattr(self, attr)
                if isinstance(attr, Setting):
                    d[attr.name] = attr.get_value()
            f.write(json.dumps(d, indent=2))
