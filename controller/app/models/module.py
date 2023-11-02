from typing import List
from . import Setting


class Module:
    name: str
    enabled: Setting = Setting(
        "enabled", bool, False, "Whether the module is enabled", "true"
    )

    def write_to_state():
        pass
