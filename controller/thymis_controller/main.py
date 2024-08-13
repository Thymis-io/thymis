import importlib
import logging

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.environment import EnvironmentContext
import thymis_controller.lib  # pylint: disable=unused-import
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from thymis_controller.routers import api, frontend, auth
from thymis_controller.config import global_settings

# run database migrations
config = Config('alembic.ini')
script = ScriptDirectory.from_config(config)

def run_migrations_offline():
    context = EnvironmentContext(config, script)
    context.configure(url=global_settings.DATABASE_URL, target_metadata=None, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

run_migrations_offline()

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
    servers=[
        {
            "url": global_settings.BASE_URL,
            "description": "Thymis Controller",
        },
    ],
    lifespan=frontend.lifespan,
)

origins = [
    # TODO remove development origins
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

app.include_router(auth.router, prefix="/auth")
app.include_router(api.router, prefix="/api")
app.include_router(frontend.router)


if importlib.util.find_spec("thymis_enterprise"):
    import thymis_enterprise  # pylint: disable=import-error # type: ignore

    thymis_enterprise.thymis_enterprise_hello_world()
