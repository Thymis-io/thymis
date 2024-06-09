import importlib
import logging

import thymis_controller.lib  # pylint: disable=unused-import
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from thymis_controller.routers import api, frontend

description = """
API to control Nix operating system 🎛️
"""

app = FastAPI(
    title="Thymis Controller API",
    description=description,
    summary="Controller backend for gathering and changing information of a device",
    version="0.1.0",
    contact={
        "name": "Thymis",
        "url": "https://thymis.io",
        "email": "software@thymis.io",
    },
    license_info={
        "name": "AGPLv3",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
    lifespan=frontend.lifespan,
)

origins = [
    "http://localhost",
    "http://localhost:5173",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api.router, prefix="/api")
app.include_router(frontend.router)


if importlib.util.find_spec("thymis_enterprise"):
    import thymis_enterprise  # pylint: disable=import-error # type: ignore

    thymis_enterprise.thymis_enterprise_hello_world()
