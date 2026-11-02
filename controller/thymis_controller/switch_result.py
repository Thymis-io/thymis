"""Interpret switch results reported by agents of different versions.

`switch-to-configuration` can exit non-zero *after* the activation succeeded:
exit 4 when units fail to reload or restart (dbus-broker is the usual one on a
25.11 -> 26.05 switch), and exit 1 when it aborts on a later systemd/logind
error (for example "Failed to get GID for root" during user activation). The
device already runs the new generation, so that switch is a success and only
needs a reboot to finish.

Current agents apply that rule themselves. Older agents still compare the exit
code to zero and report a failed switch, so the controller applies the same
rule here, using the activation marker and systemd-run status lines the agent
forwards in `stderr`. A failure that happened before activation (a failed
pre-switch check, a missing executable) or a failed activate script has no
activation marker and stays a failure, as does a switch that rolled back
because the agent could not reconnect.
"""

import re

ACTIVATION_MARKER = "activating the configuration..."
ACTIVATION_FAILURE_MARKER = "Failed to run activate script"
ROLLBACK_MARKER = "Reloading old configuration, cannot connect using new configuration"

_SYSTEMD_RUN_EXIT_STATUS = re.compile(
    r"Main processes terminated with: code=exited, status=(\d+)/"
)


def _activation_succeeded(stderr: str) -> bool:
    return (
        ACTIVATION_MARKER in stderr
        and ACTIVATION_FAILURE_MARKER not in stderr
        and ROLLBACK_MARKER not in stderr
    )


def systemd_run_exit_status(stderr: str) -> int | None:
    """The unit's exit status from `systemd-run --wait` output, if present."""
    statuses = _SYSTEMD_RUN_EXIT_STATUS.findall(stderr)
    if not statuses:
        return None
    # the last one belongs to the switch unit, not to an earlier unit
    return int(statuses[-1])


def reboot_reason_from_stderr(stderr: str) -> str:
    """A human-readable reason for a reboot-recommended switch result."""
    status = systemd_run_exit_status(stderr)
    if status == 100:
        return "the new configuration has a different init"
    if status is not None:
        return (
            f"switch-to-configuration exited {status} after activation; "
            "units may not have been restarted"
        )
    return "a reboot is recommended to finish the update"


def interpret_switch_result(
    *, is_activated: bool | None, switch_success: bool, stderr: str
) -> tuple[bool, bool, bool]:
    """Interpret an agent-reported switch result.

    Returns ``(is_activated, switch_success, reboot_required)``.

    ``is_activated=None`` (agents before the field was added) falls back to the
    activation marker in ``stderr``.
    """
    activated = (
        is_activated if is_activated is not None else _activation_succeeded(stderr)
    )
    if ACTIVATION_FAILURE_MARKER in stderr or ROLLBACK_MARKER in stderr:
        # never trust a stale/incorrect flag over an activation that failed
        # or was rolled back
        activated = False
    if switch_success:
        return activated, True, False

    status = systemd_run_exit_status(stderr)
    tolerated = activated and status is not None and status != 0
    return activated, tolerated, tolerated
