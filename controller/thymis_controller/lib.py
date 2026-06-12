from __future__ import annotations

import base64
import logging
import os
from typing import TYPE_CHECKING

import uvicorn.logging

if TYPE_CHECKING:
    from thymis_controller.models.state import Config, State

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = uvicorn.logging.DefaultFormatter(
    fmt="%(levelprefix)s %(asctime)s: %(name)s: %(message)s"
)
ch.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[ch])
logger = logging.getLogger(__name__)


HOST_PRIORITY = 80


class StringFilter(logging.Filter):
    def __init__(self, endpoint: str, summary_after_n: int = 100):
        super().__init__()
        self.endpoint = endpoint
        self.summary_after_n = summary_after_n
        self.count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        if record.getMessage().find(self.endpoint) != -1:
            self.count += 1
            if self.count % self.summary_after_n == 0:
                logger.info(
                    "Received %d logs containing %s: %s",
                    self.count,
                    self.endpoint,
                    record.getMessage(),
                )
            return False
        return True


logging.getLogger("uvicorn.access").addFilter(
    StringFilter('"POST /agent/logs HTTP/1.1" 200')
)


def read_into_base64(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            extension = os.path.splitext(path)[1][1:]

            if extension == "svg":
                extension = "svg+xml"

            return f"data:image/{extension};base64,{encoded}"
    except FileNotFoundError:
        logger.error("File not found: %s", path)
    return None


def sanitize_hostname(name: str | None) -> str | None:
    """Sanitize a display name into a valid RFC 1123 hostname label.

    Returns None if the name is empty or produces no valid characters.
    """
    if not name or not name.strip():
        return None
    hostname = name.strip().lower()
    hostname = "".join(c if c.isalnum() or c == "-" else "-" for c in hostname)[:63]
    # RFC 1123: labels must not start or end with a hyphen
    hostname = hostname.strip("-")
    return hostname if hostname else None


def effective_hostname(
    deployment_info_name: str | None, config_device_name: str
) -> str:
    """Per-device name → config default → 'thymis'. Never empty."""
    return (
        sanitize_hostname(deployment_info_name)
        or sanitize_hostname(config_device_name)
        or "thymis"
    )


def get_config_device_name(config: Config | None, state: State | None = None) -> str:
    """Return the effective device_name for a config, merging tag sources by priority.

    Mirrors lib.mkOverride semantics: lowest priority number wins.
    Config modules use HOST_PRIORITY (80); tags use their own priority field.
    Returns '' when no source provides a non-empty value.
    """
    if config is None:
        return ""

    candidates: list[tuple[int, str]] = []  # (priority, value)

    for ms in config.modules:
        if "ThymisDevice" in ms.type:
            val = ms.settings.get("device_name", "") or ""
            if val:
                candidates.append((HOST_PRIORITY, val))

    if state is not None:
        for tag in state.tags:
            if tag.identifier in config.tags:
                for ms in tag.modules:
                    if "ThymisDevice" in ms.type:
                        val = ms.settings.get("device_name", "") or ""
                        if val:
                            candidates.append((tag.priority, val))

    if not candidates:
        return ""
    return min(candidates, key=lambda c: c[0])[1]
