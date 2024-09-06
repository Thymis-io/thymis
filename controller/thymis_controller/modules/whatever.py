import thymis_controller.modules.modules as modules
from thymis_controller import models


class WhateverModule(modules.Module):
    display_name: str = "Custom Module"

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
        self, f, module_settings: models.ModuleSettings, priority: int
    ):
        settings = (
            module_settings.settings["settings"]
            if "settings" in module_settings.settings
            else self.settings.default
        )

        f.write(settings)
