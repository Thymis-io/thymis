import json
import os
from abc import ABC
from pathlib import Path
from typing import Optional

from thymis_controller import models, modules
from thymis_controller.nix import convert_python_value_to_nix

from .settings import Setting, StringSetting


def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def load_locales(file_location, language):
    try:
        domain = Path(file_location).stem
        locale_dir = Path(file_location).parent.resolve() / "locales"
        with open(locale_dir / Path(f"{domain}.{language}.json")) as f:
            locales = json.load(f)
        locales = flatten_dict(locales)
        return locales
    except:
        return {}


class Module(ABC):
    displayName: str
    icon: Optional[str] = None

    localization: modules.settings.LocalizationProvider | None = None

    def get_model(self, language) -> models.Module:
        locales = self.localization.load_locales(language) if self.localization else {}

        # collect all settings
        settings = {}
        for attr in dir(self):
            if not attr.startswith("_"):
                value = getattr(self, attr)
                if isinstance(value, modules.modules.Setting):
                    settings[attr] = value.get_model(locales)
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
            try:
                my_attr = getattr(self, attr)
            except AttributeError:
                import traceback

                traceback.print_exc()
                print(f"Attribute {attr} not found in {self}")
                continue
            assert isinstance(my_attr, models.Setting)
            if isinstance(my_attr.type, models.ListType):
                continue
            f.write(
                f"  {my_attr.name} = lib.mkOverride {priority} {convert_python_value_to_nix(value)};\n"
            )


# TODO: remove the following blocks of code
from .kiosk import Kiosk
from .oci_container import OCIContainers
from .thymis import ThymisController, ThymisDevice
from .whatever import WhateverModule

ALL_MODULES: list[Module] = [
    ThymisDevice(),
    ThymisController(),
    WhateverModule(),
    Kiosk(),
    OCIContainers(),
]

ALL_MODULES_START = ALL_MODULES.copy()
