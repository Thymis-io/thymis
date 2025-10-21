import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import convert_python_value_to_nix
from thymis_controller.project import Project


class BashModule(modules.Module):
    display_name: str = "Bash Module"

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CustomCoding.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CustomCoding_dark.svg")
    )

    timer_config = modules.Setting(
        display_name=modules.LocalizedString(
            en="Timer Configuration",
            de="Timer Konfiguration",
        ),
        type=modules.SystemdTimerType(),
        default=None,
        description="The timer configuration for the bash script.",
        example="",
        order=10,
    )

    script = modules.Setting(
        display_name=modules.LocalizedString(
            en="Freeform Settings",
            de="Freiform Einstellungen",
        ),
        type=modules.TextAreaCodeType(
            language="bash",
        ),
        default="",
        description="The settings for the freeform module.",
        example="",
        order=20,
    )

    @staticmethod
    def generate_timer_settings(timer_config: models.SystemdTimerType):
        settings = []
        if timer_config.timer_type == "realtime":
            for calendar in timer_config.on_calendar or []:
                if calendar:
                    settings.append(f'timerConfig.OnCalendar = "{calendar}";')
            if timer_config.persistent:
                settings.append(
                    f"timerConfig.Persistent = {convert_python_value_to_nix(timer_config.persistent)};"
                )
        elif timer_config.timer_type == "monotonic":
            if timer_config.on_boot_sec:
                settings.append(
                    f'timerConfig.OnBootSec = "{timer_config.on_boot_sec}";'
                )
            if timer_config.on_unit_active_sec:
                settings.append(
                    f'timerConfig.OnUnitActiveSec = "{timer_config.on_unit_active_sec}";'
                )
        if timer_config.accuracy_sec:
            settings.append(f'timerConfig.AccuracySec = "{timer_config.accuracy_sec}";')
        if timer_config.randomized_delay_sec:
            settings.append(
                f'timerConfig.RandomizedDelaySec = "{timer_config.randomized_delay_sec}";'
            )
        return settings

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        # unique-enough service name, based on the config/tag type + name
        service_name = "thymis-bash-service-" + (
            str(path.relative_to(project.path / "repository"))
            .replace("/", "-")
            .replace(".", "-")
        )

        bash_script = module_settings.settings.get(
            "script", self.script.default
        ).strip()

        timer_config_raw = module_settings.settings.get(
            "timer_config", self.timer_config.default
        )
        if timer_config_raw is not None:
            timer_config = models.SystemdTimerType.model_validate(timer_config_raw)
            timer_settings = self.generate_timer_settings(timer_config)
        else:
            timer_settings = []

        f.write(
            f"""
            systemd.services."{service_name}" = {{
                script = ''
{bash_script}
                '';
                serviceConfig = {{
                    Type = "oneshot";
                }};
            }};
            systemd.timers."{service_name}" = {{
                wantedBy = [ "timers.target" ];
                {"\n    ".join(timer_settings)}
            }};
            """.strip()
        )
