import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix import convert_python_value_to_nix


class ThymisController(modules.Module):
    display_name: str = "Thymis Controller"

    repo_dir = modules.Setting(
        display_name=modules.LocalizedString(
            en="Repository Path",
            de="Repository Pfad",
        ),
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The path to the repository.",
            de="Der Pfad zum Repository.",
        ),
        nix_attr_name="services.thymis-controller.repo-path",
        example="/var/lib/thymis/repository",
        order=10,
    )
    database_url = modules.Setting(
        display_name=modules.LocalizedString(
            en="Database URL",
            de="Datenbank URL",
        ),
        nix_attr_name="services.thymis-controller.database-url",
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The URL to the database.",
            de="Die URL zur Datenbank.",
        ),
        example="sqlite:////var/lib/thymis/thymis.sqlite",
        order=20,
    )
    base_url = modules.Setting(
        display_name=modules.LocalizedString(
            en="Base URL",
            de="Basis URL",
        ),
        nix_attr_name="services.thymis-controller.base-url",
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The base URL of the controller.",
            de="Die Basis URL des Controllers.",
        ),
        example="http://localhost:8000",
        order=30,
    )
    auth_basic = modules.Setting(
        display_name=modules.LocalizedString(
            en="Basic Auth",
            de="Basic Auth",
        ),
        nix_attr_name="services.thymis-controller.auth-basic",
        type="bool",
        default=None,
        description=modules.LocalizedString(
            en="Enable basic authentication.",
            de="Aktiviere Basic Authentifizierung.",
        ),
        example="true",
        order=40,
    )
    auth_basic_username = modules.Setting(
        display_name=modules.LocalizedString(
            en="Basic Auth Username",
            de="Basic Auth Benutzername",
        ),
        nix_attr_name="services.thymis-controller.auth-basic-username",
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The username for basic authentication.",
            de="Der Benutzername für die Basic Authentifizierung.",
        ),
        example="admin",
        order=50,
    )
    auth_basic_password_file = modules.Setting(
        display_name=modules.LocalizedString(
            en="Basic Auth Password File",
            de="Basic Auth Passwort Datei",
        ),
        nix_attr_name="services.thymis-controller.auth-basic-password-file",
        type="path",
        default=None,
        description=modules.LocalizedString(
            en="The path to the password file for basic authentication.",
            de="Der Pfad zur Passwortdatei für die Basic Authentifizierung.",
        ),
        example="/var/lib/thymis/auth-basic-password",
        order=60,
    )
    listen_host = modules.Setting(
        display_name=modules.LocalizedString(
            en="Listen Host",
            de="Listen Host",
        ),
        nix_attr_name="services.thymis-controller.listen-host",
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The host to listen on.",
            de="Der Host, auf dem gehört werden soll.",
        ),
        example="127.0.0.1",
        order=70,
    )
    listen_port = modules.Setting(
        display_name=modules.LocalizedString(
            en="Listen Port",
            de="Listen Port",
        ),
        nix_attr_name="services.thymis-controller.listen-port",
        type="int",
        default=None,
        description=modules.LocalizedString(
            en="The port to listen on.",
            de="Der Port, auf dem gehört werden soll.",
        ),
        example="8000",
        order=80,
    )
    nginx_vhost_enable = modules.Setting(
        display_name=modules.LocalizedString(
            en="Enable Nginx Vhost",
            de="Nginx Vhost aktivieren",
        ),
        nix_attr_name="services.thymis-controller.nginx-vhost-enable",
        type="bool",
        default=None,
        description=modules.LocalizedString(
            en="Enable the Nginx vhost.",
            de="Aktiviere den Nginx Vhost.",
        ),
        example="true",
        order=90,
    )
    nginx_vhost_name = modules.Setting(
        display_name=modules.LocalizedString(
            en="Nginx Vhost Name",
            de="Nginx Vhost Name",
        ),
        nix_attr_name="services.thymis-controller.nginx-vhost-name",
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The name of the Nginx vhost.",
            de="Der Name des Nginx Vhosts.",
        ),
        example="thymis",
        order=100,
    )

    def write_nix_settings(
        self, f, module_settings: models.ModuleSettings, priority: int
    ):
        f.write(f"  imports = [\n")
        f.write(f"    inputs.thymis.nixosModules.thymis-controller\n")
        f.write(f"  ];\n")
        f.write("  services.thymis-controller.enable = true;\n")

        return super().write_nix_settings(f, module_settings, priority)


class ThymisDevice(modules.Module):
    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "hard-drive-thymis.png")
    )

    display_name: str = "Core Device Configuration"

    device_type = modules.Setting(
        display_name=modules.LocalizedString(
            en="Device Type",
            de="Gerätetyp",
        ),
        nix_attr_name="thymis.config.device-type",
        type=modules.SelectOneType(
            select_one=[
                ("generic-x86_64", "generic-x86_64"),
                ("raspberry-pi-3", "raspberry-pi-3"),
                ("raspberry-pi-4", "raspberry-pi-4"),
                ("raspberry-pi-5", "raspberry-pi-5"),
                ("generic-aarch64", "generic-aarch64"),
            ]
        ),
        default="",
        description=modules.LocalizedString(
            en="The type of device.",
            de="Der Typ des Geräts.",
        ),
        example="",
        order=10,
    )

    device_name = modules.Setting(
        display_name=modules.LocalizedString(
            en="Hostname",
            de="Hostname",
        ),
        nix_attr_name="thymis.config.device-name",
        type="string",
        default="",
        description=modules.LocalizedString(
            en="The hostname of the device.",
            de="Der Hostname des Geräts.",
        ),
        example="",
        order=20,
    )

    nix_state_version = modules.Setting(
        display_name=modules.LocalizedString(
            en="NixOS State Version",
            de="NixOS State Version",
        ),
        nix_attr_name="system.stateVersion",
        type=modules.SelectOneType(select_one=["24.05"]),
        default="24.05",
        description=modules.LocalizedString(
            en="The NixOS state version.",
            de="Die NixOS Zustandsversion.",
        ),
        example="",
        order=25,
    )

    password = modules.Setting(
        display_name=modules.LocalizedString(
            en="Root Password",
            de="Root Passwort",
        ),
        nix_attr_name="thymis.config.password",
        type="string",
        default="",
        description=modules.LocalizedString(
            en="The root password of the device.",
            de="Das Root-Passwort des Geräts.",
        ),
        example="",
        order=30,
    )

    wifi_ssid = modules.Setting(
        display_name=modules.LocalizedString(
            en="WiFi SSID",
            de="WiFi SSID",
        ),
        nix_attr_name="thymis.config.wifi-ssid",
        type="string",
        default="",
        description=modules.LocalizedString(
            en="The SSID of the WiFi network.",
            de="Die SSID des WLAN-Netzwerks.",
        ),
        example="",
        order=40,
    )

    wifi_password = modules.Setting(
        display_name=modules.LocalizedString(
            en="WiFi Password",
            de="WiFi Passwort",
        ),
        nix_attr_name="thymis.config.wifi-password",
        type="string",
        default="",
        description=modules.LocalizedString(
            en="The password of the WiFi network.",
            de="Das Passwort des WLAN-Netzwerks.",
        ),
        example="",
        order=50,
    )

    authorized_keys = modules.Setting(
        display_name=modules.LocalizedString(
            en="Authorized Keys",
            de="Authorisierte Schlüssel",
        ),
        nix_attr_name="thymis.config.authorized-keys",
        type=modules.ListType(
            settings={
                "key": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Key",
                        de="Schlüssel",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The authorized key.",
                        de="Der authorisierte Schlüssel.",
                    ),
                    example="ssh-rsa AAAA...",
                )
            },
            element_name=modules.LocalizedString(
                en="Key name",
                de="Schlüsselname",
            ),
        ),
        default=None,
        description=modules.LocalizedString(
            en="Authorized keys.",
            de="Authorisierte Schlüssel.",
        ),
        example="",
        order=60,
    )

    def write_nix_settings(
        self, f, module_settings: models.ModuleSettings, priority: int
    ):
        device_type = (
            module_settings.settings["device_type"]
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        authorized_keys = (
            module_settings.settings["authorized_keys"]
            if "authorized_keys" in module_settings.settings
            else self.authorized_keys.default
        )

        if device_type:
            f.write(f"  imports = [\n")
            f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            f.write(f"  ];\n")

        if authorized_keys:
            key_list = convert_python_value_to_nix(
                list(map(lambda x: x["key"] if "key" in x else None, authorized_keys)),
                ident=1,
            )
            f.write(
                f"  users.users.root.openssh.authorizedKeys.keys = lib.mkOverride {priority} {key_list};\n"
            )

        return super().write_nix_settings(f, module_settings, priority)
