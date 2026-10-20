import pathlib

HARDWARE_ID_FILE_PATHS = {
    "pi-serial-number": "/sys/firmware/devicetree/base/serial-number",
    "dmi-board-serial": "/sys/class/dmi/id/board_serial",
    "dmi-product-uuid": "/sys/class/dmi/id/product_uuid",
}

AGENT_TOKEN_FILENAME = "thymis-token.txt"
DEFAULT_DATA_PATH = pathlib.Path("/etc/thymis")
AGENT_DATA_PATHS = [
    pathlib.Path("/boot/firmware"),  # raspberry-pi-nix generated sd-cards
    pathlib.Path("/boot"),  # boot.loader.efi.efiSysMountPoint
    DEFAULT_DATA_PATH,  # non-nixos systems
]

AGENT_TOKEN_EXPECTED_FORMAT = (
    "thymis-[0-9a-f]{128}"  # see controller/thymis_controller/task/worker.py `token =`
)


AGENT_METADATA_FILENAME = "thymis-metadata.json"
CONTROLLER_PUBLIC_KEY_FILENAME = "thymis-controller-ssh-pubkey.txt"
ROOT_AUTHORIZED_KEYS_PATH = "/root/.ssh/authorized_keys"
DEVICE_HOSTNAME_FILENAME = "thymis-hostname.txt"
HOSTNAME_PATH = pathlib.Path("/etc/hostname")
DEFAULT_HOSTNAME = "thymis"
