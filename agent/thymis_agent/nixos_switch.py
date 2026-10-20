"""Switching the device to a new NixOS system configuration."""

import asyncio
import os

CURRENT_SYSTEM_PATH = "/run/current-system"
SYSTEM_PROFILE = "/nix/var/nix/profiles/system"
SWITCH_UNIT = "thymis-nixos-rebuild-switch-to-configuration"
ROLLBACK_UNIT = "thymis-nixos-rebuild-switch-to-configuration-rollback"


def read_current_system() -> str:
    """The store path of the running system configuration."""
    return os.readlink(CURRENT_SYSTEM_PATH)


def set_system_profile_args(config_path: str) -> list[str]:
    return ["nix-env", "-p", SYSTEM_PROFILE, "--set", config_path]


def switch_to_configuration_args(
    config_path: str, unit: str, quiet: bool = False
) -> list[str]:
    return [
        "systemd-run",
        "-E",
        "LOCALE_ARCHIVE",
        "-E",
        "NIXOS_INSTALL_BOOTLOADER=1",
        "--collect",
        "--no-ask-password",
        "--pipe",
        *(["--quiet"] if quiet else []),
        "--service-type=exec",
        f"--unit={unit}",
        "--wait",
        f"{config_path}/bin/switch-to-configuration",
        "switch",
    ]


async def run_process(args: list[str]) -> tuple[int, bytes, bytes]:
    """Run `args` to completion. Returns ``(returncode, stdout, stderr)``."""
    proc = await asyncio.create_subprocess_exec(
        args[0],
        *args[1:],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    # the process has exited, so this returns its exit code without waiting
    returncode = await proc.wait()
    return returncode, stdout, stderr


def interpret_switch_result(returncode: int, stderr: str) -> tuple[bool, bool]:
    """Interpret a finished `switch-to-configuration switch`.

    Returns ``(is_activated, switch_success)``.

    ``switch-to-configuration`` exits 4 when units failed to reload or restart
    *after* the activation succeeded (dbus-broker is the usual one: on the
    25.11 -> 26.05 transition its reload times out after 90 s). The device is on
    the new configuration in that case, so a fully switched device must not be
    reported as a failed switch.
    """
    is_activated = (
        "activating the configuration..." in stderr
        and "Failed to run activate script" not in stderr
    )
    switch_success = returncode == 0
    if not switch_success and is_activated and returncode == 4:
        switch_success = True
    return is_activated, switch_success


def switch_needs_reboot(returncode: int, is_activated: bool) -> bool:
    """True when the configuration is active but a reboot is needed to finish.

    That is the tolerated non-zero exit of `switch-to-configuration`: units
    failed to reload/restart, so the new generation is on disk and the profile
    switched, but running services still come from the old generation.
    """
    return bool(is_activated and returncode != 0)
