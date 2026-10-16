from __future__ import annotations

import base64
import logging
import os
import unicodedata

import uvicorn.logging

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
    hostname = name.strip().casefold()
    hostname = unicodedata.normalize("NFKD", hostname)
    hostname = hostname.encode("ascii", "ignore").decode()
    hostname = "".join(c if c.isalnum() or c == "-" else "-" for c in hostname)
    hostname = "-".join(part for part in hostname.split("-") if part)
    hostname = hostname[:63]
    # RFC 1123: labels must not start or end with a hyphen
    hostname = hostname.strip("-")
    return hostname if hostname else None
