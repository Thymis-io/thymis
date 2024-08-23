from enum import Enum


class DeviceType(str, Enum):
    generic_x86_64 = "generic-x86_64"
    raspberry_pi_3 = "raspberry-pi-3"
    raspberry_pi_4 = "raspberry-pi-4"
    raspberry_pi_5 = "raspberry-pi-5"
    generic_aarch64 = "generic-aarch64"


class ImageFormat(str, Enum):
    img = "img"
    iso = "iso"
    qcow2 = "qcow2"
    vhdx = "vhdx"


__all__ = ["DeviceType", "ImageFormat"]
