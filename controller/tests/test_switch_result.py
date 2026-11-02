"""Tests for interpreting switch results reported by agents.

Older agents report a non-zero `switch-to-configuration` exit after the
activation (exit 4 for failed unit reloads/restarts, exit 1 for a later
systemd/logind error) as a failed switch. The controller must recognise the
activation and the tolerated exit status in the forwarded stderr and report
the deploy as a success with a reboot required.
"""

import pytest
from thymis_controller.switch_result import interpret_switch_result

ACTIVATED_EXIT_4 = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
stopping the following units: systemd-sysctl.service
activating the configuration...
setting up /etc...
reloading the following units: -.mount, boot-firmware.mount, dbus.service
restarting the following units: dhcpcd.service, sshd.service
Failed to reload dbus-broker.service
the following new units were started: dbus-broker.service
          Finished with result: exit-code
Main processes terminated with: code=exited, status=4/NOPERMISSION
"""

ACTIVATED_EXIT_1 = ACTIVATED_EXIT_4.replace("4/NOPERMISSION", "1/FAILURE")
ACTIVATED_EXIT_2 = ACTIVATED_EXIT_4.replace("4/NOPERMISSION", "2/FAILURE")

ROLLED_BACK = """
activating the configuration...
reloading user units for root...
          Finished with result: success
Main processes terminated with: code=exited, status=0/SUCCESS

Reloading old configuration, cannot connect using new configuration
"""

MISSING_EXECUTABLE = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
          Finished with result: exit-code
Main processes terminated with: code=exited, status=203/EXEC
"""

PRE_SWITCH_CHECK_FAILED = """
Running as unit: thymis-nixos-rebuild-switch-to-configuration.service
refusing to switch: /boot/firmware cannot hold the new kernel + initrd
Pre-switch checks failed
          Finished with result: exit-code
Main processes terminated with: code=exited, status=1/FAILURE
"""

FAILED_ACTIVATION = """
activating the configuration...
Failed to run activate script
          Finished with result: exit-code
Main processes terminated with: code=exited, status=4/NOPERMISSION
"""


@pytest.mark.parametrize(
    ("is_activated", "switch_success", "stderr", "expected"),
    [
        # new agent reported the switch as successful
        (True, True, ACTIVATED_EXIT_4, (True, True, False)),
        # old agent, tolerated post-activation unit failure
        (True, False, ACTIVATED_EXIT_4, (True, True, True)),
        # old agent before the is_activated field: detect it from stderr
        (None, False, ACTIVATED_EXIT_4, (True, True, True)),
        # any other non-zero exit after activation is also tolerated
        (True, False, ACTIVATED_EXIT_1, (True, True, True)),
        (True, False, ACTIVATED_EXIT_2, (True, True, True)),
        (None, False, ACTIVATED_EXIT_1, (True, True, True)),
        # the activation script itself failed
        (True, False, FAILED_ACTIVATION, (False, False, False)),
        # switch never reached activation
        (False, False, MISSING_EXECUTABLE, (False, False, False)),
        (None, False, MISSING_EXECUTABLE, (False, False, False)),
        (False, False, PRE_SWITCH_CHECK_FAILED, (False, False, False)),
        # agent rolled back because it could not reconnect from the new config
        (False, False, ROLLED_BACK, (False, False, False)),
        (None, False, ROLLED_BACK, (False, False, False)),
        # old agent failed without forwarding systemd-run status
        (True, False, "activating the configuration...", (True, False, False)),
        (True, False, "", (True, False, False)),
    ],
)
def test_interpret_switch_result(is_activated, switch_success, stderr, expected):
    assert (
        interpret_switch_result(
            is_activated=is_activated,
            switch_success=switch_success,
            stderr=stderr,
        )
        == expected
    )
