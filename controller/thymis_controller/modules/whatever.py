from thymis_controller import models, modules
from thymis_controller.models import ModuleSettings


class WhateverModule(modules.Module):
    displayName: str = "Custom Module"

    settings = models.Setting(
        name="freeform.settings",
        type="textarea",
        default="",
        description="The settings for the freeform module.",
        example="",
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        settings = (
            module_settings.settings["settings"]
            if "settings" in module_settings.settings
            else self.settings.default
        )

        f.write(settings)
