import pathlib
from pydantic_settings import BaseSettings

class GlobalSettings(BaseSettings):
    # TODO replace attributes with Fields according to the pydantic documentation

    REPO_PATH: pathlib.Path = pathlib.Path("/var/lib/thymis")
    BASE_URL: str = "http://localhost:8000"

    FRONTEND_BINARY_PATH: str | None = None
    AUTH_BASIC: bool = True
    AUTH_BASIC_USERNAME: str = "admin"
    AUTH_BASIC_PASSWORD: str = "admin"

    AUTH_OAUTH: bool = False
    AUTH_OAUTH_CLIENT_ID: str | None = None
    AUTH_OAUTH_CLIENT_SECRET: str | None = None
    AUTH_OAUTH_AUTHORIZATION_ENDPOINT: str | None = None
    AUTH_OAUTH_TOKEN_ENDPOINT: str | None = None

    class Config:
        env_prefix = "THYMIS_"
        env_file = ".env"
        env_file_encoding = "utf-8"


global_settings = GlobalSettings()
