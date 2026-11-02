"""Switching the device to a new NixOS system configuration."""

import asyncio
import os

CURRENT_SYSTEM_PATH = "/run/current-system"
SYSTEM_PROFILE = "/nix/var/nix/profiles/system"
SWITCH_UNIT = "thymis-nixos-rebuild-switch-to-configuration"
ROLLBACK_UNIT = "thymis-nixos-rebuild-switch-to-configuration-rollback"
BOOT_ID_PATH = "/proc/sys/kernel/random/boot_id"


def read_current_system() -> str:
    """The store path of the running system configuration."""
    return os.readlink(CURRENT_SYSTEM_PATH)


def read_boot_id() -> str | None:
    """The kernel's boot id, which changes on every boot."""
    try:
        with open(BOOT_ID_PATH, encoding="utf-8") as boot_id_file:
            return boot_id_file.read().strip() or None
    except OSError:
        return None


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

    ``switch-to-configuration`` can exit non-zero *after* the activation
    succeeded: exit 4 when units failed to reload or restart (dbus-broker is
    the usual one: on the 25.11 -> 26.05 transition its reload times out after
    90 s), and exit 1 when it aborts on a later systemd/logind error. The
    device is on the new configuration in that case, so a switched device must
    not be reported as a failed switch. A failed activate script or a failure
    before activation keeps the switch a failure.
    """
    is_activated = (
        "activating the configuration..." in stderr
        and "Failed to run activate script" not in stderr
    )
    switch_success = returncode == 0 or is_activated
    return is_activated, switch_success


def switch_needs_reboot(returncode: int, is_activated: bool) -> bool:
    """True when the configuration is active but a reboot is needed to finish.

    That is any non-zero exit of `switch-to-configuration` after the
    activation: the new generation is on disk and the profile switched, but
    the remaining unit reloads/restarts did not finish.
    """
    return bool(is_activated and returncode != 0)


def changed_boot_files(current_config: str, new_config: str) -> list[str]:
    """Boot artifacts that differ between the running and the new system."""
    changed = []
    for name in ("kernel", "initrd"):
        try:
            current = os.readlink(os.path.join(current_config, name))
            new = os.readlink(os.path.join(new_config, name))
        except OSError:
            continue
        if current != new:
            changed.append(name)
    return changed


def switch_reboot_requirement(
    returncode: int,
    is_activated: bool,
    current_config: str,
    new_config: str,
) -> tuple[bool, str | None]:
    """Whether a reboot is needed after a switch and why.

    A reboot is needed when the switch did not finish after the activation
    (some units may still run the old configuration), when the new system has
    a different init interface (the switch then exits 100 and only a reboot
    activates it), or when the kernel/initrd changed and the running kernel
    keeps executing until the next boot.
    """
    reasons = []
    if returncode == 100:
        reasons.append("the new configuration has a different init")
    elif switch_needs_reboot(returncode, is_activated):
        reasons.append(
            f"switch-to-configuration exited {returncode} after activation; "
            "units may not have been restarted"
        )
    changed = changed_boot_files(current_config, new_config)
    if changed:
        reasons.append(f"{' and '.join(changed)} changed")
    if not reasons:
        return False, None
    return True, "; ".join(reasons)
