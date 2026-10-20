"""What the agent reports about the device it runs on."""

import datetime
import socket
from datetime import timezone
from typing import Any

import psutil
from thymis_agent import logger
from thymis_agent.messages import EtRMetricsMessage

HARDWARE_ID_FILE_PATHS = {
    "pi-serial-number": "/sys/firmware/devicetree/base/serial-number",
    "dmi-board-serial": "/sys/class/dmi/id/board_serial",
    "dmi-product-uuid": "/sys/class/dmi/id/product_uuid",
}


def detect_hostname() -> str:
    return socket.gethostname()


def detect_hardware_id() -> dict[str, str]:
    """The readable entries of `HARDWARE_ID_FILE_PATHS`, by name."""

    def extract_file_content(path: str) -> str | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().replace("\n", "").strip()
        except FileNotFoundError:
            logger.debug("File not found: %s", path)
            return None
        except Exception as e:
            logger.error("Failed to read file: %s", e)
            return None

    hardware_ids = {
        key: extract_file_content(path) for key, path in HARDWARE_ID_FILE_PATHS.items()
    }
    return {key: value for key, value in hardware_ids.items() if value}


def detect_ram_bytes() -> int | None:
    """Detect total RAM in bytes using psutil."""
    try:
        return psutil.virtual_memory().total
    except Exception as e:
        logger.debug("Failed to detect RAM: %s", e)
        return None


def detect_network_interfaces() -> list[dict[str, Any]]:
    interfaces: dict[str, dict[str, Any]] = {}
    for interface, snics in psutil.net_if_addrs().items():
        if interface == "lo":
            continue
        if interface not in interfaces:
            interfaces[interface] = {
                "interface": interface,
                "ipv4_addresses": [],
                "ipv6_addresses": [],
                "mac_address": None,
            }
        for snic in snics:
            if snic.family == socket.AF_INET:
                interfaces[interface]["ipv4_addresses"].append(snic.address)
            elif snic.family == socket.AF_INET6:
                interfaces[interface]["ipv6_addresses"].append(snic.address)
            elif snic.family == psutil.AF_LINK:
                interfaces[interface]["mac_address"] = snic.address
    return sorted(
        (
            {
                "interface": iface["interface"],
                "ipv4_addresses": sorted(iface["ipv4_addresses"]),
                "ipv6_addresses": sorted(iface["ipv6_addresses"]),
                "mac_address": iface["mac_address"],
            }
            for iface in interfaces.values()
        ),
        key=lambda x: x["interface"],
    )


def init_metrics() -> None:
    """psutil.cpu_percent(interval=None) measures since its previous call."""
    psutil.cpu_percent(interval=None)


def collect_metrics() -> EtRMetricsMessage:
    return EtRMetricsMessage(
        timestamp=datetime.datetime.now(timezone.utc),
        cpu_percent=psutil.cpu_percent(interval=None),
        ram_percent=psutil.virtual_memory().percent,
        disk_percent=psutil.disk_usage("/").percent,
    )
