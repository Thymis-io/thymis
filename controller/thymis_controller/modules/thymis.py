import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.config import global_settings
from thymis_controller.lib import read_into_base64
from thymis_controller.nix import convert_python_value_to_nix, template_env
from thymis_controller.project import Project


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
    ssh_key_path = modules.Setting(
        display_name=modules.LocalizedString(
            en="SSH Key Path",
            de="SSH-Key Pfad",
        ),
        nix_attr_name="services.thymis-controller.ssh-key-path",
        type="string",
        default=None,
        description=modules.LocalizedString(
            en="The path to the SSH key for deploying to devices.",
            de="Der Pfad zum SSH-Key, um auf Geräte auszurollen.",
        ),
        example="/var/lib/thymis/id_thymis",
        order=35,
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
        self, f, module_settings: models.ModuleSettings, priority: int, project: Project
    ):
        f.write(f"  imports = [\n")
        f.write(f"    inputs.thymis.nixosModules.thymis-controller\n")
        f.write(f"  ];\n")
        f.write("  services.thymis-controller.enable = true;\n")

        return super().write_nix_settings(f, module_settings, priority, project)


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
                ("Generic x86-64", "generic-x86_64"),
                ("Raspberry Pi 3", "raspberry-pi-3"),
                ("Raspberry Pi 4", "raspberry-pi-4"),
                ("Raspberry Pi 5", "raspberry-pi-5"),
                ("Generic AArch64", "generic-aarch64"),
            ],
        ),
        default="",
        description=modules.LocalizedString(
            en="The type of device.",
            de="Der Typ des Geräts.",
        ),
        example="",
        order=10,
    )

    image_format = modules.Setting(
        display_name=modules.LocalizedString(
            en="Image Format",
            de="Image Format",
        ),
        nix_attr_name="thymis.config.image-format",
        type=modules.SelectOneType(
            select_one=[
                ("SD-Card Image", "sd-card-image"),
                ("Virtual Disk Image (qcow)", "qcow"),
                ("Installation ISO", "iso"),
            ],
            extra_data={
                "restrict_values_on_other_key": {
                    "device_type": {
                        "generic-x86_64": ["qcow", "iso"],
                        "generic-aarch64": ["qcow"],
                        "raspberry-pi-3": ["sd-card-image"],
                        "raspberry-pi-4": ["sd-card-image"],
                        "raspberry-pi-5": ["sd-card-image"],
                    }
                },
            },
        ),
        default="",
        description=modules.LocalizedString(
            en="The image format.",
            de="Das Image-Format.",
        ),
        example="",
        order=15,
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
        default=[],
        description=modules.LocalizedString(
            en="Authorized keys.",
            de="Authorisierte Schlüssel.",
        ),
        example="",
        order=60,
    )

    agent_enabled = modules.Setting(
        display_name=modules.LocalizedString(
            en="Agent Enabled",
            de="Agent aktiviert",
        ),
        nix_attr_name="thymis.config.agent.enable",
        type="bool",
        default=False,
        description=modules.LocalizedString(
            en="Enable the agent, necessary for auto discover.",
            de="Aktiviert den Agent, notwendig für Auto-Discover.",
        ),
        example="",
        order=70,
    )

    agent_controller_url = modules.Setting(
        display_name=modules.LocalizedString(
            en="Thymis Controller URL",
            de="Thymis Controller-URL",
        ),
        nix_attr_name="thymis.config.agent.controller-url",
        type="string",
        default="",
        description=modules.LocalizedString(
            en="URL of this Thymis Controller instance",
            de="URL dieser Thymis Controller-Instanz",
        ),
        example="",
        order=80,
    )

    static_networks = modules.Setting(
        display_name=modules.LocalizedString(
            en="Static Network",
            de="Statisches Netzwerk",
        ),
        type=modules.ListType(
            settings={
                "interface": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Interface",
                        de="Schnittstelle",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The interface.",
                        de="Die Schnittstelle.",
                    ),
                    example="ens3",
                ),
                "ipv4address": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="IPv4",
                        de="IPv4",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The IPv4 address.",
                        de="Die IPv4 Adresse.",
                    ),
                    example="",
                ),
                "ipv4prefixLength": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="IPv4 Prefix Length",
                        de="IPv4 Präfix Länge",
                    ),
                    type="int",
                    default="",
                    description=modules.LocalizedString(
                        en="The IPv4 prefix length.",
                        de="Die IPv4 Präfix Länge.",
                    ),
                    example="",
                ),
                "ipv6address": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="IPv6",
                        de="IPv6",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The IPv6 address.",
                        de="Die IPv6 Adresse.",
                    ),
                    example="",
                ),
                "ipv6prefixLength": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="IPv6 Prefix Length",
                        de="IPv6 Präfix Länge",
                    ),
                    type="int",
                    default="",
                    description=modules.LocalizedString(
                        en="The IPv6 prefix length.",
                        de="Die IPv6 Präfix Länge.",
                    ),
                    example="",
                ),
                "gateway": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Default Gateway IPv4",
                        de="Standard Gateway IPv4",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The default gateway IPv4.",
                        de="Das Standard Gateway IPv6.",
                    ),
                    example="",
                ),
                "gateway6": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Default Gateway IPv6",
                        de="Standard Gateway IPv6",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The default gateway IPv6.",
                        de="Das Standard Gateway IPv6.",
                    ),
                    example="",
                ),
                "isDefaultGateway": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Set as Default Gateway",
                        de="Setze als Standard Gateway",
                    ),
                    type="bool",
                    default="",
                    description=modules.LocalizedString(
                        en="Set as default gateway.",
                        de="Setze als Standard Gateway.",
                    ),
                    example="",
                ),
            },
            element_name=modules.LocalizedString(
                en="Network",
                de="Netzwerk",
            ),
        ),
        default=None,
        description=modules.LocalizedString(
            en="Static network configuration.",
            de="Statische Netzwerkkonfiguration.",
        ),
        example="",
        order=90,
    )

    nameservers = modules.Setting(
        display_name=modules.LocalizedString(
            en="Nameservers",
            de="Nameserver",
        ),
        type=modules.ListType(
            settings={
                "nameserver": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Nameserver",
                        de="Nameserver",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The DNS nameserver.",
                        de="Der DNS-Nameserver.",
                    ),
                    example="",
                )
            },
            element_name=modules.LocalizedString(
                en="Nameserver",
                de="Nameserver",
            ),
        ),
        default=None,
        description=modules.LocalizedString(
            en="Nameservers",
            de="Nameserver",
        ),
        example="",
        order=100,
    )

    def write_nix_settings(
        self, f, module_settings: models.ModuleSettings, priority: int, project: Project
    ):
        device_type = (
            module_settings.settings["device_type"]
            if "device_type" in module_settings.settings
            else self.device_type.default
        )

        image_format = (
            module_settings.settings["image_format"]
            if "image_format" in module_settings.settings
            else self.image_format.default
        )

        authorized_keys = (
            module_settings.settings["authorized_keys"]
            if "authorized_keys" in module_settings.settings
            else self.authorized_keys.default
        )

        # add key at global_settings.SSH_KEY_PATH

        if (path := pathlib.Path(global_settings.SSH_KEY_PATH) / ".pub").exists():
            with path.open() as f_key:
                public_key = f_key.read().strip()
            authorized_keys.append({"key": public_key})

        static_networks = (
            module_settings.settings["static_networks"]
            if "static_networks" in module_settings.settings
            else self.static_networks.default
        )

        nameservers = (
            module_settings.settings["nameservers"]
            if "nameservers" in module_settings.settings
            else self.nameservers.default
        )

        f.write(f"  imports = [\n")

        if device_type:
            f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")

        if image_format:
            f.write(f"    inputs.thymis.nixosModules.thymis-image-{image_format}\n")

        f.write(f"  ];\n")

        if authorized_keys:
            keys = list(
                map(lambda x: x["key"] if "key" in x else None, authorized_keys)
            )
        else:
            keys = []

        if project.public_key:
            keys.append(project.public_key)

        if len(keys) > 0:
            key_list_nix = convert_python_value_to_nix(keys, ident=1)
            f.write(
                f"  users.users.root.openssh.authorizedKeys.keys = {key_list_nix};\n"
            )

        if static_networks:
            template = template_env.get_template("networking.nix.j2")

            # get first network with isDefaultGateway set to True
            default_gateway_network = next(
                (
                    network
                    for network in static_networks
                    if network.get("isDefaultGateway", False)
                ),
                None,
            )
            default_gateway = {}
            default_gateway6 = {}
            if default_gateway_network:
                if default_gateway_network.get("ipv4address"):
                    default_gateway["address"] = default_gateway_network["gateway"]
                    default_gateway["interface"] = default_gateway_network["interface"]
                if default_gateway_network.get("ipv6address"):
                    default_gateway6["address"] = default_gateway_network["gateway6"]
                    default_gateway6["interface"] = default_gateway_network["interface"]

            rt = template.render(
                {
                    **module_settings.settings,
                    "default_gateway": default_gateway,
                    "default_gateway6": default_gateway6,
                    "nameservers": nameservers,
                    "priority": priority,
                }
            )
            f.write(rt + "\n")

        return super().write_nix_settings(f, module_settings, priority, project)
