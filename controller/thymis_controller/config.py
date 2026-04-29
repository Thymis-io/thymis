import pathlib

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class GlobalSettings(BaseSettings):
    PROJECT_PATH: pathlib.Path = pathlib.Path("/var/lib/thymis")
    ALEMBIC_INI_PATH: str = f"{pathlib.Path(__file__).parent.parent}/alembic.ini"

    BASE_URL: str = "http://localhost:8000"
    AGENT_ACCESS_URL: str | None = None

    # AI Assistant settings
    AI_ASSISTANT_ENABLED: bool = False
    AI_ASSISTANT_API_URL: str = "https://api.openai.com/v1"
    AI_ASSISTANT_API_KEY: str = ""
    AI_ASSISTANT_MODEL: str = "gpt-4o"
    AI_ASSISTANT_SYSTEM_PROMPT: str = """You are a Thymis AI assistant that helps users configure and manage NixOS IoT devices.
Thymis is a platform for managing and configuring IoT devices using NixOS. Key concepts:
- Devices: Physical or virtual machines managed by Thymis (Raspberry Pi, x86, etc.)
- Configurations: Named sets of module settings applied to devices
- Tags: Groups of modules that can be applied to multiple configurations
- Modules: Reusable components that define settings (e.g., Core Device Configuration, Kiosk)
- Deployments: The process of building and pushing NixOS configurations to devices
- Secrets: Encrypted values deployed to devices
- Artifacts: Static files deployed to devices
- Auto-Update: Periodic flake updates and deployments

When helping users:
- Ask about device types when recommending modules
- Suggest appropriate settings based on use case (kiosk, gateway, sensor, etc.)
- Reference Thymis documentation when explaining NixOS concepts
- Provide exact module names and setting paths
- Show example NixOS config snippets when helpful"""
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

    METRICS_RETENTION_DAYS: int = 30
    METRICS_CLEANUP_INTERVAL_SECONDS: int = 60 * 60 * 24  # 24 hours

    model_config = ConfigDict(
        env_prefix="THYMIS_", env_file=".env", env_file_encoding="utf-8"
    )


global_settings = GlobalSettings()
