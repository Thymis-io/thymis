import pathlib
from typing import List, Tuple

import thymis_controller.modules.modules as modules
from pydantic import JsonValue
from thymis_controller import db_models, models
from thymis_controller.lib import read_into_base64
from thymis_controller.project import Project


class FilesModule(modules.Module):
    display_name = modules.LocalizedString(
        en="Files",
        de="Dateien",
    )

    category = modules.LocalizedString(
        en="Files",
        de="Dateien",
    )

    description = modules.LocalizedString(
        en="Deploy secrets and artifacts onto the device filesystem.",
        de="Secrets und Artifacts im Dateisystem des Geräts bereitstellen.",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "CoreDevice_dark.svg")
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
        order=10,
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
        order=20,
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
        artifacts = (
            module_settings.settings["artifacts"]
            if "artifacts" in module_settings.settings
            else self.artifacts.default
        )

        if artifacts:
            f.write("  systemd.tmpfiles.rules = [\n")
            artifact: dict
            for artifact in artifacts:
                artifact_path = artifact.get("artifact", None)
                result_path = artifact.get("path", "/") or "/"
                mode = artifact.get("mode", "-") or "-"
                user = artifact.get("owner", "-") or "-"
                group = artifact.get("group", "-") or "-"
                if artifact_path:
                    f.write(
                        f'    "C+ {result_path} {mode} {user} {group} - ${{pkgs.copyPathToStore (inputs.self + "/artifacts/{artifact_path}")}}"\n'
                    )
            f.write("  ];")

        return super().write_nix_settings(f, path, module_settings, priority, project)
