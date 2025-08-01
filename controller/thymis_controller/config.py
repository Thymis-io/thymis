import pathlib

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class GlobalSettings(BaseSettings):
    PROJECT_PATH: pathlib.Path = pathlib.Path("/var/lib/thymis")
    ALEMBIC_INI_PATH: str = f"{pathlib.Path(__file__).parent.parent}/alembic.ini"

    BASE_URL: str = "http://localhost:8000"
    AGENT_ACCESS_URL: str | None = None

    FRONTEND_BINARY_PATH: str | None = None
    AUTH_BASIC: bool = True
    AUTH_BASIC_USERNAME: str = "admin"
    AUTH_BASIC_PASSWORD_FILE: str = "/var/lib/thymis/auth-basic-password"

    AUTH_OAUTH: bool = False
    AUTH_OAUTH_CLIENT_ID: str | None = None
    AUTH_OAUTH_CLIENT_SECRET_FILE: str | None = None
    AUTH_OAUTH_AUTHORIZATION_ENDPOINT: str | None = None
    AUTH_OAUTH_TOKEN_ENDPOINT: str | None = None
    AUTH_OAUTH_CLIENT_ROLE_LOGIN: str | None = None
    AUTH_OAUTH_INTROSPECTION_ENDPOINT: str | None = None

    LOG_RETENTION_DAYS: int = 7
    LOG_CLEANUP_INTERVAL_SECONDS: int = 60 * 60  # 1 hour

    model_config = ConfigDict(
        env_prefix="THYMIS_", env_file=".env", env_file_encoding="utf-8"
    )


global_settings = GlobalSettings()
