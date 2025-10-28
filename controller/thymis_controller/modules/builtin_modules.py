from .bash import BashModule
from .kiosk import Kiosk
from .modules import Module
from .oci_container import OCIContainers
from .python import PythonModule
from .thymis import ThymisDevice
from .whatever import WhateverModule

ALL_MODULES: list[Module] = [
    ThymisDevice(),
    OCIContainers(),
    Kiosk(),
    WhateverModule(),
    BashModule(),
    PythonModule(),
]

ALL_MODULES_START = ALL_MODULES.copy()

__all__ = ["ALL_MODULES", "ALL_MODULES_START"]
