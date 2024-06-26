import os
from abc import ABC
from typing import Optional

from thymis_controller import models
from thymis_controller.nix import convert_python_value_to_nix


class Module(ABC):
    displayName: str
    icon: Optional[str] = None

    def get_model(self) -> models.Module:
        # collect all settings
        settings = {}
        for attr in dir(self):
            if not attr.startswith("_"):
                value = getattr(self, attr)
                if isinstance(value, models.Setting):
                    settings[attr] = value
        return models.Module(
            type=self.type,
            displayName=self.displayName,
            settings=settings,
            icon=self.icon,
        )

    @property
    def type(self):
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def write_nix(
        self,
        path: os.PathLike,
        module_settings: "models.ModuleSettings",
        priority: int,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+") as f:
            f.write("{ pkgs, lib, inputs, ... }:\n")
            f.write("{\n")

            self.write_nix_settings(f, module_settings, priority)

            f.write("}\n")

    def write_nix_settings(
        self, f, module_settings: "models.ModuleSettings", priority: int
    ):
        for attr, value in module_settings.settings.items():
            my_attr = getattr(self, attr)
            assert isinstance(my_attr, models.Setting)
            f.write(
                f"  {my_attr.name} = lib.mkOverride {priority} {convert_python_value_to_nix(value)};\n"
            )


# TODO: remove the following blocks of code
from .kiosk import Kiosk
from .node_red import NodeRed
from .screenshotmodules import Grafana1Module, MqttxModule, NodeRedModule
from .thymis import ThymisController, ThymisDevice
from .whatever import WhateverModule

ALL_MODULES: list[Module] = [
    NodeRed(),
    ThymisController(),
    ThymisDevice(),
    WhateverModule(),
    Kiosk(),
    Grafana1Module(),
    NodeRedModule(),
    MqttxModule(),
]

ALL_MODULES_START = ALL_MODULES.copy()
