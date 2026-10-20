import asyncio
import datetime
import logging
import os
import subprocess
import sys

from thymis_agent import logger
from thymis_agent.agent import Agent
from thymis_agent.constants import DEFAULT_HOSTNAME
from thymis_agent.controller_key import (
    load_controller_public_key_into_root_authorized_keys,
    refresh_controller_public_key,
    store_controller_public_key,
)
from thymis_agent.device_secrets import place_stored_secrets
from thymis_agent.enrollment import enroll, get_pairing_code_arg
from thymis_agent.hostname import apply_hostname, read_hostname
from thymis_agent.rsyslog import (
    reload_rsyslog_sync,
    schedule_rsyslog_reload_on_activation,
    write_rsyslog_config,
)
from thymis_agent.storage import find_agent_metadata, find_agent_token, get_device_nonce
from thymis_agent.systemd import SystemdNotifier


def set_minimum_time(datetime_str: str) -> None:
    time = datetime.datetime.now()
    metadata_time = datetime.datetime.fromisoformat(datetime_str)
    if time < metadata_time:
        subprocess.run(["date", "-s", datetime_str])


def place_secrets_on_start(
    controller_host: str, token: str | None, just_place_secrets: bool
) -> None:
    # use message if there, if not
    # try using thymis-secrets-initial.json and decrypting using token,
    if token is not None:
        changed = write_rsyslog_config(controller_host, token)
        if changed:
            logger.info("Rsyslog config changed, reloading")
            if just_place_secrets:
                schedule_rsyslog_reload_on_activation()
            else:
                reload_rsyslog_sync()

    place_stored_secrets(token)


def enroll_with_pairing_code(
    controller_host: str, systemd_notifier: SystemdNotifier
) -> str:
    pairing_code = get_pairing_code_arg()
    nonce = get_device_nonce()
    if not (pairing_code and nonce):
        logger.error(
            "Agent token not found and no pairing code provided, cannot connect to controller"
        )
        sys.exit(1)
    agent_token, controller_public_key = enroll(
        controller_host, pairing_code, nonce, systemd_notifier
    )
    if controller_public_key:
        store_controller_public_key(controller_public_key)
    return agent_token


def prepare_device(
    controller_host: str,
    token: str | None,
    manage_hostname: bool,
    default_hostname: str,
    just_place_secrets: bool,
) -> None:
    load_controller_public_key_into_root_authorized_keys()
    if manage_hostname:
        # before place_secrets_on_start, so the rsyslog config gets the applied hostname
        apply_hostname(read_hostname(default_hostname))
    place_secrets_on_start(controller_host, token, just_place_secrets)


def main() -> None:
    agent_metadata = find_agent_metadata()

    if not agent_metadata:
        logging.error("Agent metadata not found, continuing without metadata")

    controller_host = os.getenv("CONTROLLER_HOST")

    if not controller_host:
        raise ValueError("CONTROLLER_HOST environment variable is required")

    manage_hostname = os.getenv("MANAGE_HOSTNAME", "").lower() in ("1", "true", "yes")
    default_hostname = os.getenv("DEFAULT_HOSTNAME", "").strip() or DEFAULT_HOSTNAME

    logger.setLevel(logging.INFO)
    if agent_metadata:
        set_minimum_time(agent_metadata["datetime"])

    systemd_notifier = SystemdNotifier()
    just_place_secrets = "--just-place-secrets" in sys.argv

    agent_token = find_agent_token()
    if just_place_secrets:
        if agent_token:
            refresh_controller_public_key(controller_host, agent_token)
        prepare_device(
            controller_host, agent_token, manage_hostname, default_hostname, True
        )
        return

    if agent_token:
        refresh_controller_public_key(controller_host, agent_token)
    else:
        agent_token = enroll_with_pairing_code(controller_host, systemd_notifier)
    prepare_device(
        controller_host, agent_token, manage_hostname, default_hostname, False
    )
    agent = Agent(
        controller_host,
        agent_token,
        agent_metadata,
        systemd_notifier,
        manage_hostname=manage_hostname,
        default_hostname=default_hostname,
    )
    asyncio.run(agent.async_main())


if __name__ == "__main__":
    main()
