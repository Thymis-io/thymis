import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller.lib import read_into_base64


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
        str(pathlib.Path(__file__).parent / "icons" / "Localization.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "Localization_dark.svg")
    )

    settings_namespace = "localization"
    nix_derivation = "localization"

    timezone = modules.Setting(
        display_name=modules.LocalizedString(
            en="Timezone",
            de="Zeitzone",
        ),
        nix_attr_name="thymis.config.localization.timezone",
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
        nix_attr_name="thymis.config.localization.time-servers",
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
