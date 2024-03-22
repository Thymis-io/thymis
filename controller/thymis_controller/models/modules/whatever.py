from thymis_controller.models import Module, Setting
from thymis_controller.models.setting import ModuleSettings


class WhateverModule(Module):
    settings: Setting = Setting(
        name="freeform.settings",
        type="textarea",
        default="",
        description="The settings for the freeform module.",
        example="",
    )

    def write_nix_settings(self, f, module_settings: ModuleSettings, priority: int):
        settings = (
            module_settings.settings["settings"].value
            if "settings" in module_settings.settings
            else self.settings.default
        )

        f.write(settings)
