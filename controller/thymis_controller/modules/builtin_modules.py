from thymis_controller.models.module import Module

from .kiosk import Kiosk
from .oci_container import OCIContainers
from .thymis import ThymisController, ThymisDevice
from .whatever import WhateverModule

ALL_MODULES: list[Module] = [
    ThymisDevice(),
    ThymisController(),
    WhateverModule(),
    Kiosk(),
    OCIContainers(),
]

ALL_MODULES_START = ALL_MODULES.copy()

__all__ = ["ALL_MODULES", "ALL_MODULES_START"]
