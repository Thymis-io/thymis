from thymis_controller.models.state import ModuleSettings
from thymis_controller.modules import modules


class RaspberryPi4(modules.Module):
    display_name: str = "Raspberry Pi 4"

    audio_enable = modules.Setting(
        display_name=modules.LocalizedString(
            en="Audio",
            de="Audio",
        ),
        type="bool",
        default="false",
        description="Enable or disable audio.",
        example="false",
        order=20,
    )

    def write_nix_settings(
        self,
        f,
        module_settings: ModuleSettings,
        priority: int,
        project: modules.Project,
    ):
        audio_enable = (
            module_settings.settings["audio_enable"]
            if "audio_enable" in module_settings.settings
            else self.audio_enable.default
        )

        if audio_enable:
            f.write('hardware.raspberry-pi."4".audio.enable = true;\n')
            f.write("sound.enable = true;\n")

        return super().write_nix_settings(f, module_settings, priority, project)
