import os

from thymis_controller import models, modules
from thymis_controller.nix import template_env


class OCIContainers(modules.Module):
    displayName: str = "OCI Containers"

    containers: models.Setting = models.Setting(
        name="oci-containers.containers",
        type=models.ListType(
            settings={
                "container_name": models.Setting(
                    name="oci-containers.containerSettings.container-name",
                    type="string",
                    default="",
                    description="The name of the container.",
                    example="",
                    order=10,
                ),
                "image": models.Setting(
                    name="oci-containers.containerSettings.image",
                    type="string",
                    default="",
                    description="The image of the container.",
                    example="",
                    order=15,
                ),
                "ports": models.Setting(
                    name="oci-containers.containerSettings.ports",
                    type=models.ListType(
                        settings={
                            "host": models.Setting(
                                name="oci-containers.containerSettings.portSettings.host",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                            "container": models.Setting(
                                name="oci-containers.containerSettings.portSettings.container",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                        }
                    ),
                    default=[],
                    description="The ports to expose in the container.",
                    example=None,
                    order=25,
                ),
                "volumes": models.Setting(
                    name="oci-containers.containerSettings.volumes",
                    type=models.ListType(
                        settings={
                            "host": models.Setting(
                                name="oci-containers.containerSettings.volumeSettings.host",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                            "container": models.Setting(
                                name="oci-containers.containerSettings.volumeSettings.container",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                        }
                    ),
                    default=[],
                    description="The volumes to mount in the container.",
                    example=None,
                    order=30,
                ),
                "environment": models.Setting(
                    name="oci-containers.containerSettings.environment",
                    type=models.ListType(
                        settings={
                            "key": models.Setting(
                                name="oci-containers.containerSettings.environmentSettings.key",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                            "value": models.Setting(
                                name="oci-containers.containerSettings.environmentSettings.value",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                        }
                    ),
                    default=[],
                    description="The environment variables to set in the container.",
                    example='[""]',
                    order=35,
                ),
                "labels": models.Setting(
                    name="oci-containers.containerSettings.labels",
                    type=models.ListType(
                        settings={
                            "key": models.Setting(
                                name="oci-containers.containerSettings.labelSettings.key",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                            "value": models.Setting(
                                name="oci-containers.containerSettings.labelSettings.value",
                                type="string",
                                default="",
                                description="",
                                example="",
                            ),
                        }
                    ),
                    default=[],
                    description="The labels to set in the container.",
                    example='[""]',
                    order=40,
                ),
            }
        ),
        default=[],
        description="The containers to run.",
        example=None,
        order=10,
    )

    def write_nix(
        self,
        path: os.PathLike,
        module_settings: "models.ModuleSettings",
        priority: int,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+") as f:
            template = template_env.get_template("oci_container.nix.j2")

            rt = template.render({**module_settings.settings, "priority": priority})
            f.write(rt)
