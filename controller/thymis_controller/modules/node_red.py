import pathlib
from typing import Optional

from thymis_controller import lib, models, modules


class NodeRed(modules.Module):
    displayName: str = "Node-RED"
    icon: Optional[str] = lib.read_into_base64(
        pathlib.Path(__file__).parent / "icons/Node-RED.svg"
    )

    enable = models.Setting(
        name="services.node-red.enable",
        type="bool",
        default=False,
        description="Whether to enable the Node-RED service.",
        example="true",
    )

    enable2 = models.Setting(
        name="services.node-red.enable",
        type="bool",
        default=False,
        description="Whether to enable the Node-RED service.",
        example="true",
    )
