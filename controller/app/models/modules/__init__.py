# import all modules from this path
from .minio import Minio
from .node_red import NodeRed
from .thymis import ThymisController, ThymisDevice
from .whatever import WhateverModule

ALL_MODULES = [
    Minio(),
    NodeRed(),
    ThymisController(),
    ThymisDevice(),
    WhateverModule(),
]
