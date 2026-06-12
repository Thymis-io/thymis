import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import template_env
from thymis_controller.project import Project

# list of (one of "WPA-PSK", "WPA-EAP", "IEEE8021X", "NONE", "WPA-NONE", "FT-PSK",
# "FT-EAP", "FT-EAP-SHA384", "WPA-PSK-SHA256", "WPA-EAP-SHA256", "SAE", "FT-SAE",
# "WPA-EAP-SUITE-B", "WPA-EAP-SUITE-B-192", "OSEN", "FILS-SHA256", "FILS-SHA384",
# "FT-FILS-SHA256", "FT-FILS-SHA384", "OWE", "DPP")
ALL_PROTOCOLS = [
    "WPA-PSK",
    "WPA-EAP",
    "IEEE8021X",
    "NONE",
    "WPA-NONE",
    "FT-PSK",
    "FT-EAP",
    "FT-EAP-SHA384",
    "WPA-PSK-SHA256",
    "WPA-EAP-SHA256",
    "SAE",
    "FT-SAE",
    "WPA-EAP-SUITE-B",
    "WPA-EAP-SUITE-B-192",
    "OSEN",
    "FILS-SHA256",
    "FILS-SHA384",
    "FT-FILS-SHA256",
    "FT-FILS-SHA384",
    "OWE",
    "DPP",
]


class NetworkingModule(modules.Module):
    display_name = modules.LocalizedString(
        en="Networking",
        de="Netzwerk",
    )

    category = modules.LocalizedString(
        en="Connectivity",
        de="Konnektivität",
    )

    description = modules.LocalizedString(
        en="WiFi credentials, static IP addresses and DNS nameservers.",
        de="WLAN-Zugangsdaten, statische IP-Adressen und DNS-Nameserver.",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice_dark.svg")
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
        order=10,
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
        order=20,
    )

    wifi_auth = modules.Setting(
        display_name=modules.LocalizedString(
            en="WiFi Auth (wpa_supplicant config)",
            de="WiFi Auth (wpa_supplicant config)",
        ),
        nix_attr_name="thymis.config.wifi-auth",
        type="textarea",
        default="",
        description=modules.LocalizedString(
            en="""The WiFi authentication configuration. E.g. for WPA2-Enterprise networks.

Mutually exclusive with `wifi_password`.

Example:
```
eap=PEAP
identity="user@example.com"
password="example_password"
ca_file="/etc/ssl/certs/ca-certificates.crt" # uses system ca (default mozilla) with user certs
```
""",
            de="""Die WiFi-Authentifizierungskonfiguration. Für bspw. WPA2-Enterprise-Netzwerke.

Gegenseitig ausschließend mit `wifi_password`.

Beispiel:
```
eap=PEAP
identity="user@example.com"
password="example_password"
ca_file="/etc/ssl/certs/ca-certificates.crt" # uses system ca (default mozilla) with user certs
```
""",
        ),
        example="",
        order=30,
    )

    wifi_auth_protocols = modules.Setting(
        display_name=modules.LocalizedString(
            en="WiFi Auth Protocols",
            de="WiFi Auth Protokolle",
        ),
        nix_attr_name="thymis.config.wifi-auth-protocols",
        type=modules.ListType(
            settings={
                "protocol": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Protocol",
                        de="Protokoll",
                    ),
                    type=modules.SelectOneType(
                        select_one=ALL_PROTOCOLS,
                    ),
                    default="WPA-PSK",
                    description=modules.LocalizedString(
                        en="The WiFi authentication protocol.",
                        de="Das WiFi-Authentifizierungsprotokoll.",
                    ),
                    example="",
                )
            },
            element_name=modules.LocalizedString(
                en="Protocol",
                de="Protokoll",
            ),
        ),
        default=[],
        description=modules.LocalizedString(
            en="The WiFi authentication protocols accepted by this network, siehe key_mgmt option in wpa_supplicant",
            de="Die WiFi-Authentifizierungsprotokolle, die von diesem Netzwerk akzeptiert werden, siehe key_mgmt option in wpa_supplicant",
        ),
        example="",
        order=40,
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
        order=50,
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
        order=60,
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
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
                    "static_networks": static_networks,
                    "default_gateway": default_gateway,
                    "default_gateway6": default_gateway6,
                    "nameservers": nameservers,
                    "priority": priority,
                }
            )
            f.write(rt + "\n")

        # wifi_* settings are written via their nix_attr_name by the base implementation
        return super().write_nix_settings(f, path, module_settings, priority, project)
