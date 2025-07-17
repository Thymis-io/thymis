import pathlib

import thymis_controller.modules.modules as modules
from thymis_controller import models
from thymis_controller.lib import read_into_base64
from thymis_controller.nix.templating import template_env
from thymis_controller.project import Project


class OCIContainers(modules.Module):
    display_name = modules.LocalizedString(
        en="OCI Containers",
        de="OCI Container",
    )

    icon: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "Containers.svg")
    )

    icon_dark: str = read_into_base64(
        str(pathlib.Path(__file__).parent / "icons" / "Containers_dark.svg")
    )

    containers = modules.Setting(
        display_name=modules.LocalizedString(
            en="Containers",
            de="Container",
        ),
        type=modules.ListType(
            settings={
                "container_name": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Container Name",
                        de="Container Name",
                    ),
                    type="string",
                    description=modules.LocalizedString(
                        en="The name of the container.",
                        de="Der Name des Containers.",
                    ),
                    order=10,
                ),
                "image": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Image",
                        de="Image",
                    ),
                    type="string",
                    description="The image of the container.",
                    order=15,
                ),
                "ports": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Ports",
                        de="Ports",
                    ),
                    type=modules.ListType(
                        settings={
                            "host": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Host",
                                    de="Host",
                                ),
                                type="string",
                            ),
                            "container": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Container",
                                    de="Container",
                                ),
                                type="string",
                            ),
                        },
                        element_name=modules.LocalizedString(
                            en="Port",
                            de="Port",
                        ),
                    ),
                    default=[],
                    description=modules.LocalizedString(
                        en="Container ports to expose/publish on the host.",
                        de="Ports des Containers, die auf dem Host freigegeben werden.",
                    ),
                    example=None,
                    order=25,
                ),
                "volumes": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Volumes",
                        de="Volumes",
                    ),
                    type=modules.ListType(
                        settings={
                            "host": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Host",
                                    de="Host",
                                ),
                                type="string",
                            ),
                            "container": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Container",
                                    de="Container",
                                ),
                                type="string",
                            ),
                        },
                        element_name=modules.LocalizedString(
                            en="Volume",
                            de="Volume",
                        ),
                    ),
                    default=[],
                    description=modules.LocalizedString(
                        en="The volumes to mount in the container.",
                        de="Die Volumes, die im Container gemountet werden sollen.",
                    ),
                    example=None,
                    order=30,
                ),
                "environment": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Environment Variables",
                        de="Umgebungsvariablen",
                    ),
                    type=modules.ListType(
                        settings={
                            "key": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Key/Name",
                                    de="Schlüssel/Name",
                                ),
                                type="string",
                            ),
                            "value": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Value",
                                    de="Wert",
                                ),
                                type="string",
                            ),
                        },
                        element_name=modules.LocalizedString(
                            en="Environment Variable",
                            de="Umgebungsvariable",
                        ),
                    ),
                    description=modules.LocalizedString(
                        en="The environment variables to set in the container.",
                        de="Die Umgebungsvariablen, die im Container gesetzt werden sollen.",
                    ),
                    order=35,
                ),
                "labels": modules.Setting(
                    display_name=modules.LocalizedString(
                        en="Labels",
                        de="Labels",
                    ),
                    type=modules.ListType(
                        settings={
                            "key": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Key",
                                    de="Schlüssel",
                                ),
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                            "value": modules.Setting(
                                display_name=modules.LocalizedString(
                                    en="Value",
                                    de="Wert",
                                ),
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                        },
                        element_name=modules.LocalizedString(
                            en="Label",
                            de="Label",
                        ),
                    ),
                    default=[],
                    description=modules.LocalizedString(
                        en="The labels to set in the container.",
                        de="Die Labels, die im Container gesetzt werden sollen.",
                    ),
                    example='[""]',
                    order=40,
                ),
            },
            element_name=modules.LocalizedString(
                en="Container",
                de="Container",
            ),
        ),
        default=[],
        description=modules.LocalizedString(
            en="The containers to run.",
            de="Die Container, die ausgeführt werden sollen.",
        ),
        example=None,
        order=10,
    )

    def write_nix(
        self,
        path,
        module_settings: "models.ModuleSettings",
        priority: int,
        project: Project,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+") as f:
            template = template_env.get_template("oci_container.nix.j2")

            rt = template.render({**module_settings.settings, "priority": priority})
            f.write(rt)
