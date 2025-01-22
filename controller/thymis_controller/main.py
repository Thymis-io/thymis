import importlib
import logging
import pathlib
import secrets
import subprocess
from contextlib import asynccontextmanager

import sqlalchemy.orm
import thymis_controller.lib  # pylint: disable=unused-import
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from thymis_controller.config import global_settings
from thymis_controller.database.connection import create_sqlalchemy_engine
from thymis_controller.notifications import NotificationManager
from thymis_controller.project import Project
from thymis_controller.routers import agent, api, auth, frontend
from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)

# run database migrations
alembic_config = Config(global_settings.ALEMBIC_INI_PATH)
script = ScriptDirectory.from_config(alembic_config)


def peform_db_upgrade():
    engine = create_sqlalchemy_engine()

    with engine.begin() as connection:
        alembic_config.attributes["connection"] = connection
        logger.info("Performing database upgrade")
        command.upgrade(alembic_config, "head")
        logger.info("Database upgrade complete")


def init_password_file():
    if not global_settings.AUTH_BASIC:
        return
    password_file = pathlib.Path(global_settings.AUTH_BASIC_PASSWORD_FILE)
    if not password_file.exists():
        # generate a random password and log it to the user
        password = secrets.token_urlsafe(32)
        logger.warning(
            "Password file not found at %s, generating a new one with password: %s",
            password_file,
            password,
        )
        with password_file.open("w", encoding="utf-8") as f:
            f.write(password)
        password_file.chmod(0o600)
    else:
        password = password_file.read_text(encoding="utf-8")
        logger.info(
            "Password file found at %s, using the password inside", password_file
        )


def init_ssh_key():
    if not (global_settings.PROJECT_PATH / "id_thymis").exists():
        logger.warning(
            "SSH key not found at %s, generating a new one",
            global_settings.PROJECT_PATH / "id_thymis",
        )

        # generate a new ssh key with subprocess
        keygen_process = subprocess.run(
            [
                "ssh-keygen",
                "-t",
                "ed25519",
                "-f",
                global_settings.PROJECT_PATH / "id_thymis",
                "-N",
                "",
                "-C",
                "thymis-controler",
            ],
            capture_output=True,
            text=True,
        )
        if keygen_process.returncode != 0:
            logger.error(f"Failed to generate SSH key: {keygen_process.stderr}")
            return
        logger.info(
            "SSH key generated at %s", global_settings.PROJECT_PATH / "id_thymis"
        )
        return

    # ssh key exists
    logger.info("SSH key found at %s", global_settings.PROJECT_PATH / "id_thymis")

    check_process = subprocess.run(
        [
            "ssh-keygen",
            "-y",
            "-f",
            global_settings.PROJECT_PATH / "id_thymis",
            "-P",
            "",
        ],
        capture_output=True,
        text=True,
    )

    if check_process.returncode != 0:
        logger.error(f"Failed to verify SSH key: {check_process.stderr}")
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    peform_db_upgrade()
    init_password_file()
    init_ssh_key()
    notification_manager = NotificationManager()
    notification_manager.start()
    task_controller = TaskController()
    db_engine = create_sqlalchemy_engine()
    with sqlalchemy.orm.Session(db_engine) as db_session:
        project = Project(global_settings.PROJECT_PATH.resolve(), db_session)
    async with task_controller.start(db_engine):
        logger.debug("starting frontend")
        await frontend.frontend.run()
        logger.debug("frontend started")
        logger.info("Starting controller at \033[1m%s\033[0m", global_settings.BASE_URL)
        yield {
            "notification_manager": notification_manager,
            "task_controller": task_controller,
            "project": project,
            "engine": db_engine,
        }
    notification_manager.stop()
    logger.info("stopping frontend")
    await frontend.frontend.stop()
    logger.info("frontend stopped")


description = """
API to control Nix operating system 🎛️
"""


app = FastAPI(
    title="Thymis Controller API",
    description=description,
    summary="Controller backend for gathering and changing information of a device",
    version="0.2.0",
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
    lifespan=lifespan,
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

app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)

app.include_router(auth.router, prefix="/auth")
app.include_router(api.router, prefix="/api")
app.include_router(agent.router, prefix="/agent")
app.include_router(frontend.router)


if importlib.util.find_spec("thymis_enterprise"):
    import thymis_enterprise  # pylint: disable=import-error # type: ignore

    thymis_enterprise.thymis_enterprise_hello_world()
