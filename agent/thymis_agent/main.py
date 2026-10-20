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
from thymis_agent.enrollment import enroll, get_pairing_code_arg
from thymis_agent.storage import find_agent_metadata, find_agent_token, get_device_nonce
from thymis_agent.systemd import SystemdNotifier


def set_minimum_time(datetime_str: str):
    time = datetime.datetime.now()
    metadata_time = datetime.datetime.fromisoformat(datetime_str)
    if time < metadata_time:
        subprocess.run(["date", "-s", datetime_str])


def main():
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

    agent_token = find_agent_token()
    if "--just-place-secrets" not in sys.argv and not agent_token:
        pairing_code = get_pairing_code_arg()
        nonce = get_device_nonce()
        if pairing_code and nonce:
            agent_token, controller_public_key = enroll(
                controller_host, pairing_code, nonce, systemd_notifier
            )
            if controller_public_key:
                store_controller_public_key(controller_public_key)
        else:
            logger.error(
                "Agent token not found and no pairing code provided, cannot connect to controller"
            )
            sys.exit(1)
    elif agent_token:
        refresh_controller_public_key(controller_host, agent_token)
    load_controller_public_key_into_root_authorized_keys()
    agent = Agent(
        controller_host,
        agent_token,
        agent_metadata,
        systemd_notifier,
        manage_hostname=manage_hostname,
        default_hostname=default_hostname,
    )
    if manage_hostname:
        # before place_secrets_on_start, so the rsyslog config gets the applied hostname
        agent.apply_hostname(agent.read_hostname())
    agent.place_secrets_on_start(agent_token)
    if "--just-place-secrets" not in sys.argv:
        asyncio.run(agent.async_main())


if __name__ == "__main__":
    main()
