import pathlib

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class GlobalSettings(BaseSettings):
    # TODO replace attributes with Fields according to the pydantic documentation

    REPO_PATH: pathlib.Path = pathlib.Path("/var/lib/thymis/repository")

    # TODO better input check
    DATABASE_URL: str = (
        f"sqlite:///{pathlib.Path('/var/lib/thymis/thymis.sqlite').as_posix()}"
    )
    ALEMBIC_INI_PATH: str = f"{pathlib.Path(__file__).parent.parent}/alembic.ini"

    BASE_URL: str = "http://localhost:8000"

    SSH_KEY_PATH: pathlib.Path = pathlib.Path("/var/lib/thymis/id_thymis")

    FRONTEND_BINARY_PATH: str | None = None
    AUTH_BASIC: bool = True
    AUTH_BASIC_USERNAME: str = "admin"
    AUTH_BASIC_PASSWORD_FILE: str = "/var/lib/thymis/auth-basic-password"

    AUTH_OAUTH: bool = False
    AUTH_OAUTH_CLIENT_ID: str | None = None
    AUTH_OAUTH_CLIENT_SECRET: str | None = None
    AUTH_OAUTH_AUTHORIZATION_ENDPOINT: str | None = None
    AUTH_OAUTH_TOKEN_ENDPOINT: str | None = None

    model_config = ConfigDict(
        env_prefix="THYMIS_", env_file=".env", env_file_encoding="utf-8"
    )


global_settings = GlobalSettings()
