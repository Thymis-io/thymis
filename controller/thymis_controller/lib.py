import base64
import logging
import os

import uvicorn.logging

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = uvicorn.logging.DefaultFormatter(
    fmt="%(levelprefix)s %(asctime)s: %(name)s: %(message)s"
)
ch.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[ch])
logger = logging.getLogger(__name__)


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


def read_into_base64(path: str):
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
