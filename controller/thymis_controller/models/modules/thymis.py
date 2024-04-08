import json
import os
from thymis_controller.models.setting import ModuleSettings
from jinja2 import Environment
from thymis_controller.models import Module, Setting

import pathlib

from thymis_controller import models


class ThymisController(Module):
    displayName: str = "Thymis Controller"

    repo_dir: Setting = Setting(
        name="thymis.controller.repo-dir",
        type="string",
        default="/var/lib/thymis",
        description="The directory where the thymis repository is located.",
        example="/var/lib/thymis",
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        f.write(f"  thymis.controller.enable = true;\n")

        return super().write_nix_settings(f, module_settings, priority)


class ThymisDevice(Module):
    displayName: str = "Thymis Device"

    device_type: Setting = Setting(
        name="thymis.config.device-type",
        type="select-one",
        options=["generic-x86_64", "raspberry-pi-4", "generic-aarch64"],
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

    wifi_ssid: Setting = Setting(
        name="thymis.config.wifi-ssid",
        type="string",
        default="",
        description="The wifi ssid of the thymis device.",
        example="",
    )

    wifi_password: Setting = Setting(
        name="thymis.config.wifi-password",
        type="string",
        default="",
        description="The wifi password of the thymis device.",
        example="",
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        device_type = (
            module_settings.settings["device_type"].value
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        if device_type:
            f.write(f"  imports = [\n")
            f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            f.write(f"  ];\n")

        return super().write_nix_settings(f, module_settings, priority)
