from .bash import BashModule
from .files import FilesModule
from .kiosk import Kiosk
from .localization import LocalizationModule
from .modules import Module
from .networking import NetworkingModule
from .oci_container import OCIContainers
from .python import PythonModule
from .security import SecurityAccessModule
from .thymis import ThymisDevice
from .whatever import WhateverModule

ALL_MODULES: list[Module] = [
    ThymisDevice(),
    NetworkingModule(),
    LocalizationModule(),
    SecurityAccessModule(),
    FilesModule(),
    OCIContainers(),
    Kiosk(),
    WhateverModule(),
    BashModule(),
    PythonModule(),
]

ALL_MODULES_START = ALL_MODULES.copy()

__all__ = ["ALL_MODULES", "ALL_MODULES_START"]
