import pathlib
from typing import List, Tuple

import thymis_controller.modules.modules as modules
from pydantic import JsonValue
from thymis_controller import db_models, models
from thymis_controller.config import global_settings
from thymis_controller.lib import read_into_base64
from thymis_controller.nix import convert_python_value_to_nix, template_env
from thymis_controller.project import Project


class ThymisDevice(modules.Module):
    display_name: str = "Core Device Configuration"

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice_dark.svg")
    )

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
            ],
            extra_data={
                "only_editable_on_target_type": ["config"],
            },
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
                ("USB Stick Installer", "usb-stick-installer"),
                ("NixOS VM", "nixos-vm"),
            ],
            extra_data={
                "restrict_values_on_other_key": {
                    "device_type": {
                        "generic-x86_64": ["nixos-vm", "usb-stick-installer"],
                        "raspberry-pi-3": ["sd-card-image"],
                        "raspberry-pi-4": ["sd-card-image"],
                        "raspberry-pi-5": ["sd-card-image"],
                    }
                },
                "only_editable_on_target_type": ["config"],
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
        type=modules.SelectOneType(select_one=["24.05", "24.11"]),
        default="24.11",
        description=modules.LocalizedString(
            en="The NixOS state version.",
            de="Die NixOS Zustandsversion.",
        ),
        example="",
        order=25,
    )

    password_secret = modules.Setting(
        display_name=modules.LocalizedString(
            en="Root Password",
            de="Root Passwort",
        ),
        type=modules.SecretType(
            allowed_types=[db_models.SecretTypes.SINGLE_LINE],
            default_processing_type=db_models.SecretProcessingTypes.MKPASSWD_YESCRYPT,
            default_save_to_image=True,
            on_device_path="/run/thymis/root_password_hash",
            on_device_owner="root",
            on_device_group="root",
            on_device_mode="0400",  # root only, read only, no write, no execute
        ),
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
        order=55,
    )
    # list of (one of "WPA-PSK", "WPA-EAP", "IEEE8021X", "NONE", "WPA-NONE", "FT-PSK", "FT-EAP", "FT-EAP-SHA384", "WPA-PSK-SHA256", "WPA-EAP-SHA256", "SAE", "FT-SAE", "WPA-EAP-SUITE-B", "WPA-EAP-SUITE-B-192", "OSEN", "FILS-SHA256", "FILS-SHA384", "FT-FILS-SHA256", "FT-FILS-SHA384", "OWE", "DPP")
    all_protocols = [
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
                        select_one=all_protocols,
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
        order=56,
    )

    security_pki_certificates = modules.Setting(
        display_name=modules.LocalizedString(
            en="Trusted root certificates",
            de="Vertrauenswürdige Stammzertifikate",
        ),
        type=modules.ListType(
            settings={
                "certificate": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Certificate",
                        de="Zertifikat",
                    ),
                    type="textarea",
                    default="",
                    description=modules.LocalizedString(
                        en="The certificate in PEM format.",
                        de="Das Zertifikat im PEM-Format.",
                    ),
                    example="",
                )
            },
            element_name=modules.LocalizedString(
                en="Certificate",
                de="Zertifikat",
            ),
        ),
        default=[],
        description=modules.LocalizedString(
            en="PKI certificates, available in /etc/ssl/certs/ca-certificates.crt, with mozilla ca store used as a base.",
            de="PKI-Zertifikate, verfügbar in /etc/ssl/certs/ca-certificates.crt, mit mozilla ca store als Basis.",
        ),
        order=57,
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
                    display_name="",
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
                en="Key",
                de="Schlüssel",
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

    agent_controller_url = modules.Setting(
        display_name=modules.LocalizedString(
            en="Thymis Controller URL",
            de="Thymis Controller-URL",
        ),
        # nix_attr_name="thymis.config.agent.controller-url",
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
        order=90,
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
        order=100,
    )

    secrets = modules.Setting(
        display_name=modules.LocalizedString(
            en="Secrets",
            de="Secrets",
        ),
        description=modules.LocalizedString(
            en="""Secrets to be placed on the device.

You can provide path, owner, group, mode for each secret.

Secrets are perfect for
- Passwords
- SSH keys
- TLS certificates
- Passwords
- Private keys
- Any other secret data
""",
            de="""Secrets, die auf dem Gerät platziert werden sollen.

Jedes Secret kann mit Pfad, Besitzer, Gruppe und Modus angegeben werden.
Secrets sind perfekt für
- Passwörter
- SSH-Schlüssel
- TLS-Zertifikate
- Passwörter
- Private Schlüssel
- Alle anderen geheimen Daten
""",
        ),
        type=modules.ListType(
            settings={
                "secret": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Secret",
                        de="Secret",
                    ),
                    type=modules.SecretType(
                        allowed_types=[
                            db_models.SecretTypes.SINGLE_LINE,
                            db_models.SecretTypes.MULTI_LINE,
                            db_models.SecretTypes.ENV_LIST,
                            db_models.SecretTypes.FILE,
                        ],
                        default_processing_type=db_models.SecretProcessingTypes.NONE,
                        default_save_to_image=False,
                    ),
                    default="",
                    description=modules.LocalizedString(
                        en="The secret.",
                        de="Das Secret.",
                    ),
                    example="",
                    order=0,
                ),
                "path": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Secret Path",
                        de="Secret-Pfad",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The path where the secret will be placed.",
                        de="Der Pfad, an dem das Secret abgelegt wird.",
                    ),
                    example="Secret Path",
                    order=10,
                ),
                "owner": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Owner",
                        de="Besitzer",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The owner of the secret.",
                        de="Der Besitzer des Secrets.",
                    ),
                    example="",
                    order=20,
                ),
                "group": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Group",
                        de="Gruppe",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The group of the secret.",
                        de="Die Gruppe des Secrets.",
                    ),
                    example="",
                    order=30,
                ),
                "mode": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Mode",
                        de="Modus",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The mode of the secret, bspw. 0600.",
                        de="Der Mode des Secrets, bspw. 0600.",
                    ),
                    example="",
                    order=40,
                ),
            },
            element_name=modules.LocalizedString(
                en="Secret",
                de="Secret",
            ),
        ),
        default=[],
        example="",
        order=110,
    )

    artifacts = modules.Setting(
        display_name=modules.LocalizedString(
            en="Artifacts",
            de="Artifacts",
        ),
        description=modules.LocalizedString(
            en="Artifacts to be placed on the device.",
            de="Artifacts, die auf dem Gerät platziert werden",
        ),
        type=modules.ListType(
            settings={
                "artifact": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Artifact",
                        de="Artifact",
                    ),
                    type=modules.ArtifactType(),
                    default="",
                    description=modules.LocalizedString(
                        en="The artifact.",
                        de="Das Artifact.",
                    ),
                    example="",
                    order=0,
                ),
                "path": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Path",
                        de="Pfad",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The path where the artifact will be placed.",
                        de="Der Pfad, an dem das Artifact abgelegt wird.",
                    ),
                    example="Path",
                    order=10,
                ),
                "owner": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Owner",
                        de="Besitzer",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The owner of the artifact.",
                        de="Der Besitzer des Artifacts.",
                    ),
                    example="",
                    order=20,
                ),
                "group": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Group",
                        de="Gruppe",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The group of the artifact.",
                        de="Die Gruppe des Artifacts.",
                    ),
                    example="",
                    order=30,
                ),
                "mode": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Mode",
                        de="Modus",
                    ),
                    type="string",
                    default="",
                    description=modules.LocalizedString(
                        en="The mode of the artifact, bspw. 0600.",
                        de="Der Mode des Artifacts, bspw. 0600.",
                    ),
                    example="",
                    order=40,
                ),
            },
            element_name=modules.LocalizedString(
                en="Artifact",
                de="Artifact",
            ),
        ),
        default=[],
        example="",
        order=120,
    )

    def register_secret_settings(
        self,
        module_settings: "models.ModuleSettings",
        project: Project,
    ) -> List[Tuple["modules.SecretType", JsonValue]]:
        secret_settings = super().register_secret_settings(module_settings, project)
        # for each of our list of secrets, add the secret to the secret settings
        if (
            "secrets" in module_settings.settings
            and module_settings.settings["secrets"]
        ):
            for secret in module_settings.settings["secrets"]:
                # modify type before submitting
                secret_type = self.secrets.type.settings["secret"].type
                this_secret_type = modules.SecretType(
                    **{
                        **secret_type.__dict__,
                        "on_device_path": secret["path"] if "path" in secret else None,
                        "on_device_owner": (
                            secret["owner"] if "owner" in secret else None
                        ),
                        "on_device_group": (
                            secret["group"] if "group" in secret else None
                        ),
                        "on_device_mode": secret["mode"] if "mode" in secret else None,
                    }
                )
                secret_settings.append((this_secret_type, secret["secret"]))
        return secret_settings

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        # get last 2 components of the path
        write_target_type = path.parts[-2]
        path.parts[-1]

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

        agent_controller_url = (
            module_settings.settings["agent_controller_url"]
            if "agent_controller_url" in module_settings.settings
            else self.agent_controller_url.default
        )

        security_pki_certificates = (
            module_settings.settings["security_pki_certificates"]
            if "security_pki_certificates" in module_settings.settings
            else self.security_pki_certificates.default
        )

        password_secret = (
            module_settings.settings["password_secret"]
            if "password_secret" in module_settings.settings
            else self.password_secret.default
        )

        if password_secret:
            f.write(
                f"  users.users.root.hashedPasswordFile = {convert_python_value_to_nix(self.password_secret.type.on_device_path)};\n"
            )

        f.write("  imports = [\n")

        if write_target_type == "hosts":
            if device_type:
                f.write(f"    inputs.thymis.nixosModules.thymis-device-{device_type}\n")
            if image_format:
                f.write(f"    inputs.thymis.nixosModules.thymis-image-{image_format}\n")
            elif device_type:
                first_format = self.find_image_format_by_device_type(device_type)
                f.write(f"    inputs.thymis.nixosModules.thymis-image-{first_format}\n")

        f.write("  ];\n")

        if agent_controller_url:
            f.write(
                f"  thymis.config.agent.controller-url = lib.mkOverride {priority} {convert_python_value_to_nix(agent_controller_url)};\n"
            )
        else:
            default_agent_controller_url = (
                global_settings.AGENT_ACCESS_URL or global_settings.BASE_URL or ""
            )
            f.write(
                f"  thymis.config.agent.controller-url = lib.mkOverride 100 {convert_python_value_to_nix(default_agent_controller_url)};\n"
            )

        if authorized_keys:
            keys = list(
                map(lambda x: x["key"] if "key" in x else None, authorized_keys)
            )
        else:
            keys = []

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

        if time_servers:
            servers = list(
                map(lambda x: x["server"] if "server" in x else None, time_servers)
            )
            time_servers_nix = convert_python_value_to_nix(servers, ident=1)
            f.write(f"  networking.timeServers = {time_servers_nix};\n")

        f.write(f'  time.timeZone = "{time_zone}";\n')

        if security_pki_certificates:
            certificates = list(
                map(
                    lambda x: x["certificate"] if "certificate" in x else None,
                    security_pki_certificates,
                )
            )
            security_pki_certificates_nix = convert_python_value_to_nix(
                certificates, ident=1
            )
            f.write(f"  security.pki.certificates = {security_pki_certificates_nix};\n")

        return super().write_nix_settings(f, path, module_settings, priority, project)

    def find_image_format_by_device_type(self, device_type):
        restricted = self.image_format.type.extra_data["restrict_values_on_other_key"]
        available_formats = restricted["device_type"][device_type]

        return next(
            (
                format[1]
                for format in self.image_format.type.select_one
                if format[1] in available_formats
            ),
            None,
        )
