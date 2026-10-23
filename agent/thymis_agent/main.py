import asyncio
import datetime
import logging
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

from thymis_agent import logger
from thymis_agent.agent import Agent
from thymis_agent.controller_key import (
    load_controller_public_key_into_root_authorized_keys,
    refresh_controller_public_key,
)
from thymis_agent.device_secrets import place_stored_secrets
from thymis_agent.enrollment import enroll_with_pairing_code
from thymis_agent.hostname import DEFAULT_HOSTNAME, apply_hostname, read_hostname
from thymis_agent.rsyslog import (
    schedule_rsyslog_reload_on_activation,
    write_rsyslog_config,
)
from thymis_agent.storage import find_agent_metadata, find_agent_token
from thymis_agent.systemd import SystemdNotifier


@dataclass(frozen=True)
class Settings:
    controller_host: str
    manage_hostname: bool
    default_hostname: str
    agent_metadata: dict[str, Any] | None


def set_minimum_time(datetime_str: str) -> None:
    """Never run with a clock older than the deployed configuration."""
    time = datetime.datetime.now()
    metadata_time = datetime.datetime.fromisoformat(datetime_str)
    if time < metadata_time:
        try:
            subprocess.run(["date", "-s", datetime_str], check=True)
        except (subprocess.CalledProcessError, OSError) as e:
            logger.warning("Failed to set minimum system time: %s", e)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def initialize() -> Settings:
    agent_metadata = find_agent_metadata()
    controller_host = os.getenv("CONTROLLER_HOST")
    manage_hostname = os.getenv("MANAGE_HOSTNAME", "").lower() in ("1", "true", "yes")
    default_hostname = os.getenv("DEFAULT_HOSTNAME", "").strip() or DEFAULT_HOSTNAME

    if not controller_host:
        raise ValueError("CONTROLLER_HOST environment variable is required")

    if agent_metadata and agent_metadata.get("datetime"):
        set_minimum_time(agent_metadata.get("datetime"))
    else:
        logger.warning("Agent metadata not found, continuing without metadata")

    return Settings(
        controller_host=controller_host,
        manage_hostname=manage_hostname,
        default_hostname=default_hostname,
        agent_metadata=agent_metadata,
    )


def prepare_device(settings: Settings, token: str | None) -> None:
    """Trust the controller, apply the hostname, and place the secrets."""
    load_controller_public_key_into_root_authorized_keys()
    if settings.manage_hostname:
        apply_hostname(read_hostname(settings.default_hostname))
    place_stored_secrets(token)


def place_secrets() -> None:
    """`--just-place-secrets`: prepare the device during NixOS activation.

    Works offline, so activation never waits on the controller. Syslog is
    reloaded by activation itself, after this exits.
    """
    settings = initialize()
    token = find_agent_token()
    prepare_device(settings, token)
    if token and write_rsyslog_config(settings.controller_host, token):
        schedule_rsyslog_reload_on_activation()


def run() -> None:
    """Prepare the device, then stay connected to the controller."""
    settings = initialize()
    systemd_notifier = SystemdNotifier()
    token = find_agent_token()
    if token:
        refresh_controller_public_key(settings.controller_host, token)
    else:
        token = enroll_with_pairing_code(settings.controller_host, systemd_notifier)
    prepare_device(settings, token)
    agent = Agent(
        settings.controller_host,
        token,
        settings.agent_metadata,
        systemd_notifier,
        manage_hostname=settings.manage_hostname,
        default_hostname=settings.default_hostname,
    )
    asyncio.run(agent.async_main())


def main() -> None:
    configure_logging()
    if "--just-place-secrets" in sys.argv:
        place_secrets()
    else:
        run()


if __name__ == "__main__":
    main()
