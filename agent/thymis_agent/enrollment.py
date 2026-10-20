"""Exchanging a one-time pairing code for the agent token."""

import sys
import time

import requests
from thymis_agent import logger
from thymis_agent.controller_key import store_controller_public_key
from thymis_agent.storage import get_device_nonce, update_token
from thymis_agent.systemd import SystemdNotifier


def get_pairing_code_arg() -> str | None:
    if "--pairing-code" in sys.argv:
        token_index = sys.argv.index("--pairing-code") + 1
        if token_index < len(sys.argv):
            return sys.argv[token_index]
    return None


def enroll(
    controller_host: str, code: str, nonce: str, notifier: SystemdNotifier
) -> tuple[str, str | None]:
    """A 404 is terminal; transport errors and 5xx back off and retry.

    `notifier` is pinged each attempt so systemd's 90 s start timeout (the
    unit is `Type=notify` with no `TimeoutStartSec`) does not kill a slow
    but progressing enrollment.
    """
    url = f"{controller_host.rstrip('/')}/agent/enroll"
    delay = 5
    max_delay = 60
    request_timeout = 10
    attempt = 0
    while True:
        attempt += 1
        notifier.notify(
            f"EXTEND_TIMEOUT_USEC={(delay + request_timeout + 10) * 1000 * 1000}"
        )
        notifier.status(f"Enrolling with controller (attempt {attempt})")
        try:
            response = requests.post(
                url, json={"code": code, "nonce": nonce}, timeout=request_timeout
            )
        except requests.exceptions.RequestException as e:
            logger.warning(
                "Enrollment request to %s failed: %s, retrying in %ds", url, e, delay
            )
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            continue

        if response.status_code == 404:
            logger.error(
                "Controller rejected pairing code (404); it is unknown, expired, "
                "revoked, or already consumed. Cannot enroll."
            )
            sys.exit(1)

        if response.status_code >= 500:
            logger.warning(
                "Controller returned %d during enrollment, retrying in %ds",
                response.status_code,
                delay,
            )
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            continue

        response.raise_for_status()
        body = response.json()
        token = body.get("token")
        controller_ssh_pubkey = body.get("controller_ssh_pubkey", None)
        update_token(token)
        logger.info("Enrollment successful")
        return token, controller_ssh_pubkey


def enroll_with_pairing_code(controller_host: str, notifier: SystemdNotifier) -> str:
    """Enroll using `--pairing-code`; exits when there is none."""
    pairing_code = get_pairing_code_arg()
    nonce = get_device_nonce()
    if not (pairing_code and nonce):
        logger.error(
            "Agent token not found and no pairing code provided, cannot connect to controller"
        )
        sys.exit(1)
    token, controller_public_key = enroll(
        controller_host, pairing_code, nonce, notifier
    )
    if controller_public_key:
        store_controller_public_key(controller_public_key)
    return token
