"""Tests for interpreting `switch-to-configuration switch` results.

The agent must not report a failed switch when the configuration was activated
and the remaining work failed: on the 25.11 -> 26.05 transition dbus-broker's
reload times out after 90 s (exit 4), and logind can make the user activation
abort after the system configuration is active (exit 1).
"""

import pytest
from thymis_agent.nixos_switch import (
    interpret_switch_result,
    switch_needs_reboot,
    switch_reboot_requirement,
)

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
        # units failed to reload/restart after activation: the device is switched
        (4, ACTIVATED, (True, True)),
        # switch aborted on a later error (e.g. logind during user activation):
        # the system configuration is active, only the remaining work failed
        (1, ACTIVATED, (True, True)),
        (2, ACTIVATED, (True, True)),
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


def _make_system(tmp_path, name, kernel, initrd):
    path = tmp_path / name
    path.mkdir()
    (path / "kernel").symlink_to(kernel)
    (path / "initrd").symlink_to(initrd)
    return str(path)


@pytest.mark.parametrize(
    ("returncode", "is_activated", "kernel_changed", "initrd_changed", "expected"),
    [
        (0, True, False, False, (False, None)),
        (0, True, True, False, (True, "kernel changed")),
        (0, True, False, True, (True, "initrd changed")),
        (0, True, True, True, (True, "kernel and initrd changed")),
        (4, True, False, False, (True, "exited 4 after activation")),
        (1, True, False, False, (True, "exited 1 after activation")),
        (100, False, False, False, (True, "different init")),
        (100, False, True, False, (True, "kernel changed")),
        (203, False, False, False, (False, None)),
    ],
)
def test_switch_reboot_requirement(
    tmp_path, returncode, is_activated, kernel_changed, initrd_changed, expected
):
    current = _make_system(
        tmp_path,
        "current",
        "/nix/store/old-kernel/bzImage",
        "/nix/store/old-initrd/initrd",
    )
    new = _make_system(
        tmp_path,
        "new",
        "/nix/store/new-kernel/bzImage"
        if kernel_changed
        else "/nix/store/old-kernel/bzImage",
        "/nix/store/new-initrd/initrd"
        if initrd_changed
        else "/nix/store/old-initrd/initrd",
    )

    reboot_required, reason = switch_reboot_requirement(
        returncode, is_activated, current, new
    )

    assert reboot_required is expected[0]
    if expected[1] is None:
        assert reason is None
    else:
        assert expected[1] in reason
