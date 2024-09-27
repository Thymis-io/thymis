from thymis_controller.modules.raspberry_pi_4 import RaspberryPi4

from .kiosk import Kiosk
from .modules import Module
from .oci_container import OCIContainers
from .thymis import ThymisController, ThymisDevice
from .whatever import WhateverModule

ALL_MODULES: list[Module] = [
    ThymisDevice(),
    ThymisController(),
    WhateverModule(),
    Kiosk(),
    OCIContainers(),
    RaspberryPi4(),
]

ALL_MODULES_START = ALL_MODULES.copy()

__all__ = ["ALL_MODULES", "ALL_MODULES_START"]
