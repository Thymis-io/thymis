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
