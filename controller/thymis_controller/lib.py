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
