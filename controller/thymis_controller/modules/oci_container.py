import os

from thymis_controller import models, modules
from thymis_controller.models import ModuleSettings
from thymis_controller.nix import template_env


class OCIContainer(modules.Module):
    displayName: str = "OCI Container"

    container_name = models.Setting(
        name="oci-container.config.container-name",
        type="string",
        default="",
        description="The name of the container.",
        example="",
        order=10,
    )

    image = models.Setting(
        name="oci-container.config.image",
        type="string",
        default="",
        description="The image of the container.",
        example="",
        order=15,
    )

    ports = models.Setting(
        name="oci-container.config.ports",
        type=models.ListType(
            settings={
                "host": models.Setting(
                    name="host",
                    type="string",
                    default="",
                    description="",
                    example="",
                ),
                "container": models.Setting(
                    name="container",
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
    )

    volumes = models.Setting(
        name="oci-container.config.volumes",
        type=models.ListType(
            settings={
                "host": models.Setting(
                    name="host",
                    type="string",
                    default="",
                    description="",
                    example="",
                ),
                "container": models.Setting(
                    name="container",
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
    )

    environment = models.Setting(
        name="oci-container.config.environment",
        type=models.ListType(
            settings={
                "key": models.Setting(
                    name="key",
                    type="string",
                    default="",
                    description="",
                    example="",
                ),
                "value": models.Setting(
                    name="value",
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
    )

    labels = models.Setting(
        name="oci-container.config.labels",
        type=models.ListType(
            settings={
                "key": models.Setting(
                    name="key",
                    type="string",
                    default="",
                    description="",
                    example="",
                ),
                "value": models.Setting(
                    name="value",
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
    )

    def write_nix(
        self,
        path: os.PathLike,
        module_settings: "models.ModuleSettings",
        priority: int,
    ):
        filename = f"{self.type}.nix"

        with open(path / filename, "w+") as f:
            print("AAAA", module_settings.settings)
            template = template_env.get_template("oci_container.nix.j2")

            rt = template.render(module_settings.settings)
            f.write(rt)
            # TODO priority
