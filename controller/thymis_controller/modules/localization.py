import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import convert_python_value_to_nix
from thymis_controller.project import Project


class LocalizationModule(modules.Module):
    display_name = modules.LocalizedString(
        en="Localization & Time",
        de="Lokalisierung & Zeit",
    )

    category = modules.LocalizedString(
        en="System",
        de="System",
    )

    description = modules.LocalizedString(
        en="System timezone and NTP time servers.",
        de="System-Zeitzone und NTP-Zeitserver.",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice_dark.svg")
    )

    timezone = modules.Setting(
        display_name=modules.LocalizedString(
            en="Timezone",
            de="Zeitzone",
        ),
        type="string",
        default="Europe/Berlin",
        description=modules.LocalizedString(
            en="The timezone.",
            de="Die Zeitzone.",
        ),
        example="Europe/Berlin",
        order=10,
    )

    time_servers = modules.Setting(
        display_name=modules.LocalizedString(
            en="Time Servers",
            de="Zeitserver",
        ),
        type=modules.ListType(
            settings={
                "server": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Server",
                        de="Server",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The NTP time server.",
                        de="Der NTP Zeitserver.",
                    ),
                    example="",
                )
            },
            element_name=modules.LocalizedString(
                en="Server",
                de="Server",
            ),
        ),
        default=None,
        description=modules.LocalizedString(
            en="Time servers.",
            de="Zeitserver.",
        ),
        example="",
        order=20,
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        time_servers = (
            module_settings.settings["time_servers"]
            if "time_servers" in module_settings.settings
            else self.time_servers.default
        )

        time_zone = (
            module_settings.settings["timezone"]
            if "timezone" in module_settings.settings
            else self.timezone.default
        )

        if time_servers:
            servers = list(
                map(lambda x: x["server"] if "server" in x else None, time_servers)
            )
            time_servers_nix = convert_python_value_to_nix(servers, ident=1)
            f.write(f"  networking.timeServers = {time_servers_nix};\n")

        if time_zone:
            f.write(f'  time.timeZone = "{time_zone}";\n')

        return super().write_nix_settings(f, path, module_settings, priority, project)
