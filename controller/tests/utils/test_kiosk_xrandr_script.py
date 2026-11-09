"""Behaviour of the generated xrandr watchdog.

The script is rendered by the real nix pipeline, its store paths are replaced
by fakes, and it is executed against a simulated X server. This covers the
fail-safe path that a rejected modeset used to turn into an endless
display-manager restart loop.
"""

import os
import pathlib
import re
import subprocess
import time

import pytest
from tests.utils import nix_fixture
from tests.utils.test_setting_nix_merging import _kiosk_eval
from thymis_controller import models

KIOSK = "thymis_controller.modules.kiosk.Kiosk"

FAKE_XRANDR = r"""#!/usr/bin/env python3
import os
import sys

state = os.environ["FAKE_XRANDR_STATE"]
args = sys.argv[1:]
with open(os.path.join(state, "calls.log"), "a") as f:
    f.write(" ".join(args) + "\n")

fail = os.environ.get("FAKE_XRANDR_FAIL") == "1"
mode_file = os.path.join(state, "mode")
if not os.path.exists(mode_file):
    with open(mode_file, "w") as f:
        f.write("320x200" if fail else "1920x1080")
current = open(mode_file).read().strip()

if args == ["--query"]:
    width, height = (current.split("x") + ["0"])[:2]
    # Real `xrandr --query` output: a rotation swaps the geometry, the current
    # rotation is only printed bare when it is not normal, otherwise the line
    # carries the "(" prefixed rotation list.
    rotation = os.environ.get("FAKE_XRANDR_ROTATION", "normal")
    if rotation in ("left", "right"):
        width, height = height, width
    bare = "" if rotation == "normal" else f" {rotation}"
    print(f"Screen 0: minimum 320 x 200, current {width} x {height}, maximum 2048 x 2048")
    print(f"HDMI-1 connected primary {width}x{height}+0+0{bare} (normal left inverted right x axis y axis) 1054mm x 592mm")
    print("   1920x1080     60.00 +  50.00")
    print("   1366x768      59.79")
    print("   1360x768      60.02")
elif args[:2] == ["--output", "HDMI-1"] and "--mode" in args:
    mode = args[args.index("--mode") + 1]
    if not fail:
        with open(mode_file, "w") as f:
            f.write(mode)
"""

FAKE_SYSTEMCTL = r"""#!/usr/bin/env bash
printf 'systemctl %s\n' "$*" >> "$FAKE_XRANDR_STATE/calls.log"
exit 0
"""

FAKE_CVT = r"""#!/usr/bin/env bash
printf 'cvt %s\n' "$*" >> "$FAKE_XRANDR_STATE/calls.log"
echo 'Modeline "1600x900_60.00"  119.00  1600 1696 1864 2128  900 901 904 932 -hsync +vsync'
"""

FAKE_XEV = r"""#!/usr/bin/env bash
while true; do
    echo RRScreenChangeNotify
    sleep 0.2
done
"""


def _render_script(tmp_path: pathlib.Path, mode: str, rotation: str = "normal") -> str:
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=[],
        modules=[
            models.ModuleSettings(
                type=KIOSK,
                settings={"xrandr_mode": mode, "xrandr_rotation": rotation},
            )
        ],
    )
    project = nix_fixture.render_project(tmp_path, configs=[config])
    try:
        result = _kiosk_eval(project)
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))
    return result["xrandrSetup"]


def _prepare(
    tmp_path: pathlib.Path, fail: bool, rotation: str = "normal"
) -> tuple[pathlib.Path, pathlib.Path, dict]:
    state = tmp_path / "fake-state"
    state.mkdir()
    bindir = tmp_path / "fake-bin"
    bindir.mkdir()
    home = tmp_path / "home"
    home.mkdir()

    for name, body in [
        ("xrandr", FAKE_XRANDR),
        ("systemctl", FAKE_SYSTEMCTL),
        ("cvt", FAKE_CVT),
        ("xev", FAKE_XEV),
    ]:
        path = bindir / name
        path.write_text(body)
        path.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{bindir}:{env['PATH']}"
    env["HOME"] = str(home)
    env["FAKE_XRANDR_STATE"] = str(state)
    env["FAKE_XRANDR_FAIL"] = "1" if fail else "0"
    env["FAKE_XRANDR_ROTATION"] = rotation
    env["THYMIS_XRANDR_RESTART_MARKER"] = str(tmp_path / "display-manager-restarted")
    return state, tmp_path, env


def _install_script(script: str, tmp_path: pathlib.Path) -> pathlib.Path:
    # Store paths are fixed at build time; route them through the fake bin.
    script = re.sub(
        r"/nix/store/[a-z0-9]+-[^/]+/bin/(xrandr|xev|systemctl|cvt)",
        r"\1",
        script,
    )
    path = tmp_path / "thymis-xrandr-setup"
    path.write_text(script)
    path.chmod(0o755)
    return path


def _start(path: pathlib.Path, tmp_path: pathlib.Path, env: dict) -> subprocess.Popen:
    return subprocess.Popen(
        ["bash", str(path)],
        cwd=tmp_path,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _run(
    script: str, tmp_path: pathlib.Path, env: dict, timeout: int
) -> subprocess.CompletedProcess:
    path = _install_script(script, tmp_path)
    return subprocess.run(
        ["bash", str(path)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def test_native_mode_is_used_without_cvt(tmp_path):
    script = _render_script(tmp_path / "nix", "1360x768")
    state, work, env = _prepare(tmp_path, fail=False)
    proc = _start(_install_script(script, work), work, env)
    try:
        time.sleep(12)
    finally:
        _stop(proc)

    calls = (state / "calls.log").read_text()
    assert "--mode 1360x768" in calls
    assert "cvt" not in calls
    assert "--newmode" not in calls
    assert "systemctl" not in calls


def test_healthy_normal_display_does_not_restart_display_manager(tmp_path):
    """A normal xrandr output carries the "(" prefixed rotation list, which the
    health check must strip before comparing against the configured rotation.
    Reading it as a bare token reported every healthy display unhealthy and
    restarted display-manager about once per minute."""
    script = _render_script(tmp_path / "nix", "1920x1080")
    state, work, env = _prepare(tmp_path, fail=False)
    proc = _start(_install_script(script, work), work, env)
    try:
        time.sleep(12)
    finally:
        _stop(proc)

    calls = (state / "calls.log").read_text()
    assert "--mode 1920x1080" in calls
    assert "systemctl" not in calls


def test_rotated_display_matches_the_configured_rotation(tmp_path):
    script = _render_script(tmp_path / "nix", "1920x1080", rotation="left")
    state, work, env = _prepare(tmp_path, fail=False, rotation="left")
    proc = _start(_install_script(script, work), work, env)
    try:
        time.sleep(12)
    finally:
        _stop(proc)

    calls = (state / "calls.log").read_text()
    assert "--rotate left" in calls
    assert "systemctl" not in calls


def test_fail_safe_falls_back_and_restarts_only_once(tmp_path):
    script = _render_script(tmp_path / "nix", "1360x768")
    state, work, env = _prepare(tmp_path, fail=True)
    marker = pathlib.Path(env["THYMIS_XRANDR_RESTART_MARKER"])

    _run(script, work, env, timeout=30)

    calls = (state / "calls.log").read_text()
    # The configured mode is retried, then the monitor's preferred EDID mode is
    # used as the fail-safe before one display-manager restart is attempted.
    assert calls.count("--mode 1360x768") >= 3
    assert "--mode 1920x1080" in calls
    assert calls.count("systemctl --no-block restart display-manager.service") == 1
    assert "reboot" not in calls
    assert marker.exists()

    # A restarted session (same boot) must not restart display-manager again.
    path = _install_script(script, work)
    (state / "calls.log").unlink()
    proc = _start(path, work, env)
    try:
        time.sleep(12)
    finally:
        _stop(proc)

    calls = (state / "calls.log").read_text()
    assert "systemctl" not in calls
    assert "--mode 1920x1080" in calls


def test_custom_mode_is_generated_when_edid_lacks_it(tmp_path):
    script = _render_script(tmp_path / "nix", "1600x900")
    state, work, env = _prepare(tmp_path, fail=False)
    proc = _start(_install_script(script, work), work, env)
    try:
        time.sleep(12)
    finally:
        _stop(proc)

    calls = (state / "calls.log").read_text()
    assert "cvt 1600 900 60" in calls
    assert "--newmode 1600x900_60.00" in calls
    assert "--mode 1600x900_60.00" in calls


FAKE_STALE_HOLDER = r"""#!/usr/bin/env python3
import fcntl
import os
import time

lock = os.environ["LOCK_FILE"]
f = open(lock, "w")
fcntl.flock(f, fcntl.LOCK_EX)
time.sleep(60)
"""


def _lock_holders(lock: pathlib.Path) -> set[int]:
    holders = set()
    for proc in pathlib.Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        try:
            for fd in (proc / "fd").iterdir():
                if os.readlink(fd) == str(lock):
                    holders.add(int(proc.name))
                    break
        except (FileNotFoundError, PermissionError):
            continue
    return holders


def test_stale_watchdog_of_a_previous_session_is_taken_over(tmp_path):
    """A watchdog (or its orphaned xev child) from a previous X session keeps
    the lock fd. The next session must take the lock over instead of silently
    running without a watchdog."""
    script = _render_script(tmp_path / "nix", "1920x1080")
    state, work, env = _prepare(tmp_path, fail=False)
    lock = pathlib.Path(env["HOME"]) / ".cache" / "thymis-xrandr.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)

    stale_path = tmp_path / "stale-xev"
    stale_path.write_text(FAKE_STALE_HOLDER)
    stale_path.chmod(0o755)
    stale = subprocess.Popen(
        [str(stale_path), "-root", "-event", "randr"],
        env={**os.environ, "LOCK_FILE": str(lock)},
        start_new_session=True,
    )
    deadline = time.time() + 5
    while time.time() < deadline and not _lock_holders(lock):
        time.sleep(0.1)
    assert _lock_holders(lock)

    proc = _start(_install_script(script, work), work, env)
    try:
        time.sleep(12)
        assert proc.poll() is None, "watchdog exited on the stale lock"
    finally:
        _stop(proc)
        stale.kill()
        stale.wait(timeout=5)

    calls = (state / "calls.log").read_text()
    assert "--mode 1920x1080" in calls
    assert "systemctl" not in calls


def test_xev_child_does_not_inherit_the_lock_fd(tmp_path):
    """The xev child outlives the watchdog; if it inherited the lock fd it
    would keep the lock held after the session ended."""
    script = _render_script(tmp_path / "nix", "1920x1080")
    state, work, env = _prepare(tmp_path, fail=False)
    lock = pathlib.Path(env["HOME"]) / ".cache" / "thymis-xrandr.lock"

    proc = _start(_install_script(script, work), work, env)
    try:
        time.sleep(6)
        holders = _lock_holders(lock)
        assert proc.pid in holders
        leaked = {
            pid
            for pid in holders
            if pid != proc.pid
            and (
                "xev"
                in pathlib.Path(f"/proc/{pid}/cmdline")
                .read_bytes()
                .decode(errors="replace")
                or "RRScreenChangeNotify"
                in pathlib.Path(f"/proc/{pid}/cmdline")
                .read_bytes()
                .decode(errors="replace")
            )
        }
        assert not leaked, f"lock fd leaked to xev children {leaked}"
    finally:
        _stop(proc)


def test_stale_lock_of_a_plain_child_is_waited_out(tmp_path):
    """A killed watchdog leaves a sleep child that holds the lock for its
    remaining runtime; the next session must wait it out instead of exiting."""
    script = _render_script(tmp_path / "nix", "1920x1080")
    state, work, env = _prepare(tmp_path, fail=False)
    lock = pathlib.Path(env["HOME"]) / ".cache" / "thymis-xrandr.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    stale = subprocess.Popen(
        [
            __import__("sys").executable,
            "-c",
            "import fcntl, sys, time; f = open(sys.argv[1], 'w'); "
            "fcntl.flock(f, fcntl.LOCK_EX); time.sleep(16)",
            str(lock),
        ],
        start_new_session=True,
    )
    try:
        deadline = time.time() + 5
        while time.time() < deadline and not _lock_holders(lock):
            time.sleep(0.1)
        assert _lock_holders(lock)

        proc = _start(_install_script(script, work), work, env)
        try:
            time.sleep(24)
            assert proc.poll() is None, "watchdog exited on the stale lock"
        finally:
            _stop(proc)
        calls = (state / "calls.log").read_text()
        assert "--mode 1920x1080" in calls
        assert "systemctl" not in calls
    finally:
        stale.kill()
        stale.wait(timeout=5)
