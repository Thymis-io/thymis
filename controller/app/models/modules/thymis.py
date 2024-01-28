import json
import os
from app.models.setting import ModuleSettings
from jinja2 import Environment
from app.models import Module, Setting

import pathlib

from app import models


class ThymisController(Module):
    repo_dir: Setting = Setting(
        name="thymis.config.repo-dir",
        type="string",
        default="/var/lib/thymis",
        description="The directory where the thymis repository is located.",
        example="/var/lib/thymis",
    )


class ThymisDevice(Module):
    device_type: Setting = Setting(
        name="thymis.config.device-type",
        type="string",
        default="",
        description="The device type of the thymis device.",
        example="",
    )
    device_name: Setting = Setting(
        name="thymis.config.device-name",
        type="string",
        default="",
        description="The device name of the thymis device.",
        example="",
    )
    password: Setting = Setting(
        name="thymis.config.password",
        type="string",
        default="",
        description="The password of the thymis device.",
        example="",
    )

    def write_nix(
        self,
        path: os.PathLike,
        module_settings: models.ModuleSettings,
        priority: int,
    ):
        filename = f"{self.type}.nix"

        device_type = (
            module_settings.settings["device_type"].value
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        with open(path / filename, "w+") as f:
            f.write("{ inputs, pkgs, lib, ... }:\n")
            f.write("{\n")

            f.write(f"  imports = [\n")
            # imports inputs.thymis.nixosModules.thymis-device-<device_type>
            f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            f.write(f"  ];\n")

            for attr, value in module_settings.settings.items():
                my_attr = getattr(self, attr)
                assert isinstance(my_attr, models.Setting)
                my_attr.write_nix(f, value, priority)

            f.write("}\n")
