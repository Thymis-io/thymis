"""Tests for interpreting `switch-to-configuration switch` results.

The agent must not report a failed switch when the configuration was activated
and only unit reloads/restarts failed: on the 25.11 -> 26.05 transition
dbus-broker's reload times out after 90 s, which makes switch-to-configuration
exit 4 on an otherwise fully switched device.
"""

import pytest
from thymis_agent.nixos_switch import interpret_switch_result, switch_needs_reboot

ACTIVATED = """
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

FAILED_ACTIVATION = """
activating the configuration...
Failed to run activate script
"""

NOT_ACTIVATED = """
error: cannot switch to a different systemd version
"""


@pytest.mark.parametrize(
    ("returncode", "stderr", "expected"),
    [
        # clean switch
        (0, ACTIVATED, (True, True)),
        # dbus-broker reload failure after activation: the device is switched
        (4, ACTIVATED, (True, True)),
        # any other post-activation failure must stay a failure
        (1, ACTIVATED, (True, False)),
        (2, ACTIVATED, (True, False)),
        # activation itself failed
        (1, FAILED_ACTIVATION, (False, False)),
        (4, FAILED_ACTIVATION, (False, False)),
        # switch never reached activation; exit 0 without activation is the
        # "switch success but not activated" bug the caller raises on
        (4, NOT_ACTIVATED, (False, False)),
        (0, NOT_ACTIVATED, (False, True)),
        (0, "", (False, True)),
        (4, "", (False, False)),
    ],
)
def test_interpret_switch_result(returncode, stderr, expected):
    assert interpret_switch_result(returncode, stderr) == expected


@pytest.mark.parametrize(
    ("returncode", "is_activated", "expected"),
    [
        (0, True, False),  # clean switch, nothing to do
        (4, True, True),  # tolerated dbus-broker reload failure
        (1, True, True),  # any tolerated post-activation failure needs a reboot
        (4, False, False),  # nothing was activated
        (1, False, False),
    ],
)
def test_switch_needs_reboot(returncode, is_activated, expected):
    assert switch_needs_reboot(returncode, is_activated) is expected
