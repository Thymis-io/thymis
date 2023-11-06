from . import Module, Setting


class NodeRed(Module):
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
