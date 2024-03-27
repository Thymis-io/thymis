from typing import Optional
from thymis_controller.models import Module, Setting


class NodeRed(Module):
    icon: Optional[str] = Module.read_into_base64(
        "./thymis_controller/icons/Node-RED.svg"
    )

    enable: Setting = Setting(
        name="services.node-red.enable",
        type="bool",
        default=False,
        description="Whether to enable the Node-RED service.",
        example="true",
    )

    enable2: Setting = Setting(
        name="services.node-red.enable",
        type="bool",
        default=False,
        description="Whether to enable the Node-RED service.",
        example="true",
    )
