"""
Entry point for the thymis-controller console script.

The nix wrapper (controller/default.nix) invokes uvicorn directly; this
module provides an equivalent ``main()`` so that ``uv run thymis-controller``
(used by the integration test fixture when no pre-built nix result exists)
also works.

Environment variables honoured (matching the nix wrapper defaults):
  UVICORN_HOST  — bind address  (default: 127.0.0.1)
  UVICORN_PORT  — TCP port      (default: 8000)
"""

import os

import uvicorn


def main() -> None:
    host = os.environ.get("UVICORN_HOST", "127.0.0.1")
    port = int(os.environ.get("UVICORN_PORT", "8000"))
    uvicorn.run("thymis_controller.main:app", host=host, port=port)
