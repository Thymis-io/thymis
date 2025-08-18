import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import format_nix_file
from thymis_controller.project import Project


def is_setting_whole_module(setting: str):
    # get first line that is not a comment, check if it starts with "{" or alpha-numeric
    lines = setting.splitlines()
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line.startswith("#"):
            if stripped_line.startswith("{"):
                return True
            if stripped_line and stripped_line[0].isalnum():
                return False
    return False


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
        type=modules.TextAreaCodeType(
            language="nix",
        ),
        default="",
        description="The settings for the freeform module.",
        example="",
    )

    def write_nix(self, path, module_settings, priority, project):
        settings = (
            module_settings.settings["settings"]
            if "settings" in module_settings.settings
            else self.settings.default
        )
        # check if settings is a whole module, or just a module body
        # if only body, call super, else just dump
        if is_setting_whole_module(settings):
            filename = f"{self.type}.nix"
            with open(path / filename, "w+", encoding="utf-8") as f:
                f.write(settings)
            format_nix_file(str(path / filename))
        else:
            # call super to write the module body
            super().write_nix(path, module_settings, priority, project)
        # return super().write_nix(path, module_settings, priority, project)

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
