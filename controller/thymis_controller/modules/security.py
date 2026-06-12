import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import db_models, models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import convert_python_value_to_nix
from thymis_controller.project import Project


class SecurityAccessModule(modules.Module):
    display_name = modules.LocalizedString(
        en="Security & Access",
        de="Sicherheit & Zugriff",
    )

    category = modules.LocalizedString(
        en="System",
        de="System",
    )

    description = modules.LocalizedString(
        en="Root password, authorized SSH keys and trusted root certificates.",
        de="Root-Passwort, autorisierte SSH-Schlüssel und vertrauenswürdige Stammzertifikate.",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice_dark.svg")
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
        order=10,
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
        order=20,
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
        order=30,
    )

    def write_nix_settings(
        self,
        f,
        path,
        module_settings: models.ModuleSettings,
        priority: int,
        project: Project,
    ):
        password_secret = (
            module_settings.settings["password_secret"]
            if "password_secret" in module_settings.settings
            else self.password_secret.default
        )

        authorized_keys = (
            module_settings.settings["authorized_keys"]
            if "authorized_keys" in module_settings.settings
            else self.authorized_keys.default
        )

        security_pki_certificates = (
            module_settings.settings["security_pki_certificates"]
            if "security_pki_certificates" in module_settings.settings
            else self.security_pki_certificates.default
        )

        if password_secret:
            f.write(
                f"  users.users.root.hashedPasswordFile = {convert_python_value_to_nix(self.password_secret.type.on_device_path)};\n"
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
