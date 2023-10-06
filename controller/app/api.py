from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html

description = """
API to control Nix operating system 🎛️
"""

app = FastAPI(
    title="Thymis Controller API",
    description=description,
    summary="Controller backend for gathering and changing information of a device",
    version="0.1.0",
    contact={
        "name": "Thmyis",
        "url": "https://thymis.io",
        "email": "software@thymis.io",
    },
    license_info={
        "name": "AGPLv3",
        "url": "https://www.gnu.org/licenses/agpl-3.0.en.html",
    },
)
