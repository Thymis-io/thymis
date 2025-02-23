import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.project import Project


class WhateverModule(modules.Module):
    display_name: str = "Custom Module"

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CustomCoding.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CustomCoding_dark.svg")
    )

    settings = modules.Setting(
        display_name=modules.LocalizedString(
            en="Freeform Settings",
            de="Freiform Einstellungen",
        ),
        type="textarea",
        default="",
        description="The settings for the freeform module.",
        example="",
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        settings = (
            module_settings.settings["settings"]
            if "settings" in module_settings.settings
            else self.settings.default
        )

        f.write(settings)
