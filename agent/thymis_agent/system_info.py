import datetime
import os
import socket
from collections.abc import Iterator
from datetime import timezone
from typing import Any

import psutil
from thymis_agent import logger
from thymis_agent.constants import HARDWARE_ID_FILE_PATHS
from thymis_agent.messages import EtRMetricsMessage


def detect_hostname() -> str:
    return socket.gethostname()


def detect_build_hash() -> str:
    store_path = os.readlink("/run/current-system")
    return store_path[len("/nix/store/") :].split("-")[0]


def detect_hardware_id() -> dict[str, str]:
    """
    Extracts hardware IDs from the system.

    Returns:
    dict: A dictionary containing the hardware IDs.
    """

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


def detect_ip_addresses() -> list[str]:
    def get_ip_addresses(family: socket.AddressFamily) -> Iterator[str]:
        for interface, snics in psutil.net_if_addrs().items():
            if interface == "lo":
                continue
            for snic in snics:
                if snic.family == family:
                    yield snic.address

    ipv4s = set(get_ip_addresses(socket.AF_INET))
    ipv6s = set(get_ip_addresses(socket.AF_INET6))

    return [*ipv4s, *ipv6s]


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
