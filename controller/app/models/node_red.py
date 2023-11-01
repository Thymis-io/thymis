from . import Module, Setting


class NodeRed(Module):
    enabled: Setting = Setting("services.node-red.enable", bool, False, "Whether to enable the Node-RED service.", "true")
