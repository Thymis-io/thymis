"""
Integration test for x86-64 VM build, start, deploy, and verification.

Covers the same behaviour as frontend/tests/x86_vm.spec.ts but via direct API
calls — no browser, no Playwright, no UI flake.  Useful for diagnosing CI
failures without having to wade through trace ZIPs.

Run locally
-----------
    cd controller
    THYMIS_FLAKE_ROOT=.. uv run pytest tests/integration/test_x86_vm_api.py -v -s -m integration

Requirements
------------
- ``nix build .#thymis-controller`` must have produced ``../result``
- x86-64 host with QEMU/KVM
- ``access-client`` in PATH (present in the uv venv via http-network-relay)

Design notes
------------
- ``build_device_image_task`` NEVER reaches state "completed" while its child
  ``run_nixos_vm_task`` is "running" (executor.py:204-210 only sets state=completed
  when task has no children).  Do NOT poll it for "completed".

- After the agent first connects it sends a burst of 1300+ log batches to
  POST /agent/logs.  Each handler does synchronous SQLAlchemy writes with no
  await inside the for-loop, so the single uvicorn event loop processes one
  batch at a time.  GET /api/tasks cannot get CPU for ~2–5 min during this
  window.  The test therefore sleeps AGENT_FLOOD_SETTLE_S after the VM enters
  "running" state to let the flood drain before issuing further requests.
"""

import os
import pathlib
import shutil
import socket
import subprocess
import tempfile
import time
from typing import Generator

import pytest
import requests

# ─────────────────────────────────────────────────────────────────────────────
# constants
# ─────────────────────────────────────────────────────────────────────────────

REPO_ROOT = pathlib.Path(__file__).parents[3]  # …/thymis-25.11

# Module type strings used in state JSON payloads
MOD_THYMIS_DEVICE = "thymis_controller.modules.thymis.ThymisDevice"
MOD_WHATEVER = "thymis_controller.modules.whatever.WhateverModule"
MOD_BASH = "thymis_controller.modules.bash.BashModule"

# After run_nixos_vm_task enters "running" the agent immediately sends a large
# burst of log batches which saturates the single uvicorn event loop.  Wait
# this many seconds before issuing any further requests.
AGENT_FLOOD_SETTLE_S = 150


# ─────────────────────────────────────────────────────────────────────────────
# helpers
# ─────────────────────────────────────────────────────────────────────────────


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _poll_tasks(
    session: requests.Session,
    base_url: str,
    *,
    type_filter: str,
    target_state: str,
    count: int,
    timeout: int,
    poll_interval: float = 15.0,
    request_timeout: float = 90.0,
    also_fail_on: tuple[str, ...] = (),
) -> list[dict]:
    """
    Block until at least *count* tasks of *type_filter* are in *target_state*.

    Raises AssertionError immediately if ANY task of *type_filter* OR any type
    in *also_fail_on* enters 'failed'.

    Raises TimeoutError with a summary of current task states on deadline.

    ``request_timeout`` caps each individual GET /api/tasks call.  The controller
    can become temporarily unresponsive (log flood from agent on first connect,
    or io_uring/keep-alive stall on uvicorn).  On Timeout or ConnectionError we
    close and re-open the connection (force fresh TCP) and retry immediately.
    """
    deadline = time.monotonic() + timeout
    last_progress = time.monotonic()
    while True:
        try:
            resp = session.get(
                f"{base_url}/api/tasks",
                params={"limit": 200},
                timeout=request_timeout,
            )
            resp.raise_for_status()
            all_tasks: list[dict] = resp.json()
        except requests.exceptions.Timeout:
            elapsed = int(time.monotonic() - (deadline - timeout))
            print(
                f"\n  [poll] GET /api/tasks timed out after {request_timeout}s"
                f" (elapsed {elapsed}s total) — forcing connection reset, retrying"
            )
            # Force close the connection pool so the next request gets a fresh TCP socket.
            session.close()
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Timed out after {timeout}s waiting for {count}x '{type_filter}'"
                    f" in state '{target_state}' (last attempt: request timeout)"
                )
            time.sleep(poll_interval)
            continue
        except requests.exceptions.ConnectionError as exc:
            elapsed = int(time.monotonic() - (deadline - timeout))
            print(f"\n  [poll] Connection error: {exc} (elapsed {elapsed}s) — retrying")
            session.close()
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"Timed out after {timeout}s waiting for {count}x '{type_filter}'"
                    f" in state '{target_state}' (last attempt: connection error)"
                )
            time.sleep(min(poll_interval, 5.0))
            continue

        typed = [t for t in all_tasks if t["task_type"] == type_filter]
        failed = [t for t in typed if t["state"] == "failed"]

        # also check watched types for early failure detection
        for extra_type in also_fail_on:
            extra_failed = [
                t
                for t in all_tasks
                if t["task_type"] == extra_type and t["state"] == "failed"
            ]
            failed.extend(extra_failed)

        if failed:
            lines = [
                f"  [{t['task_type']}] id={t['id']}"
                f"\n    exception: {t.get('exception') or '(none)'}"
                f"\n    stdout:    {(t.get('process_stdout') or '')[-800:]}"
                f"\n    stderr:    {(t.get('process_stderr') or '')[-800:]}"
                for t in failed
            ]
            raise AssertionError(
                f"Task(s) failed while waiting for {count}x '{type_filter}'={target_state}:\n"
                + "\n".join(lines)
            )

        matching = [t for t in typed if t["state"] == target_state]
        now = time.monotonic()
        if now - last_progress >= 30:
            state_counts: dict[str, int] = {}
            for t in typed:
                state_counts[t["state"]] = state_counts.get(t["state"], 0) + 1
            print(
                f"\n  [poll] {type_filter}={target_state}: "
                f"{len(matching)}/{count} ready. "
                f"state_counts={state_counts}. "
                f"elapsed={int(now - (deadline - timeout))}s / {timeout}s"
            )
            last_progress = now

        if len(matching) >= count:
            return matching

        if time.monotonic() > deadline:
            state_counts = {}
            for t in typed:
                state_counts[t["state"]] = state_counts.get(t["state"], 0) + 1
            raise TimeoutError(
                f"Timed out after {timeout}s waiting for {count}x '{type_filter}'"
                f" in state '{target_state}'.\n"
                f"Current counts for that type: {state_counts}\n"
                f"Total tasks in DB: {len(all_tasks)}"
            )

        time.sleep(poll_interval)


def _commit_until_clean(
    session: requests.Session, base_url: str, message: str, timeout: int = 60
) -> None:
    """
    Commit all pending changes, retrying if reload_state staged more files after the commit.

    PATCH /api/state schedules reload_state as a FastAPI background task that runs AFTER
    the response is returned.  reload_state deletes and recreates hosts/tags/modules
    dirs and calls `git add .` — all filesystem ops (< 100ms, no nix flake lock).
    A commit issued immediately after PATCH may not include those files.
    This helper retries the commit until no staged changes remain.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = session.post(f"{base_url}/api/action/commit", params={"message": message})
        assert r.status_code == 200, r.text
        time.sleep(1)  # brief window for any in-flight reload_state to finish staging
        r = session.get(f"{base_url}/api/repo_status")
        r.raise_for_status()
        if not r.json().get("changes"):
            return
    raise TimeoutError(f"Repo did not become clean within {timeout}s")


# ─────────────────────────────────────────────────────────────────────────────
# fixture: live controller subprocess
# ─────────────────────────────────────────────────────────────────────────────

ControllerInfo = tuple[str, requests.Session, int, pathlib.Path]
"""(base_url, authenticated_session, port, project_tmpdir)"""


@pytest.fixture(scope="module")
def controller() -> Generator[ControllerInfo, None, None]:
    """
    Start a real uvicorn controller in a temp directory with a real task worker.
    Yields ``(base_url, session, port, project_path)``.
    The session is already authenticated via Basic auth.
    """
    tmpdir = pathlib.Path(tempfile.mkdtemp(prefix="thymis-integ-"))
    port = _free_port()
    passwd = "integrationtest"

    passwd_file = tmpdir / "auth-basic-password"
    passwd_file.write_text(passwd)

    flake_root = os.environ.get("THYMIS_FLAKE_ROOT", str(REPO_ROOT))

    env = os.environ.copy()
    env.update(
        {
            "THYMIS_PROJECT_PATH": str(tmpdir),
            "THYMIS_AUTH_BASIC_PASSWORD_FILE": str(passwd_file),
            # disables systemd-run for QEMU so VMs work outside a systemd session
            "RUNNING_IN_PLAYWRIGHT": "true",
            # address VMs use to reach the controller from inside QEMU
            "THYMIS_AGENT_ACCESS_URL": f"http://10.0.2.2:{port}",
            "THYMIS_BASE_URL": f"http://localhost:{port}",
            "UVICORN_HOST": "127.0.0.1",
            "UVICORN_PORT": str(port),
            "THYMIS_FLAKE_ROOT": flake_root,
        }
    )

    # prefer the pre-built nix result; fall back to uv run
    result_bin = REPO_ROOT / "result" / "bin" / "thymis-controller"
    cmd = (
        [str(result_bin)] if result_bin.exists() else ["uv", "run", "thymis-controller"]
    )

    log_path = tmpdir / "controller.log"
    log_file = log_path.open("w")

    proc = subprocess.Popen(
        cmd,
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(REPO_ROOT / "controller"),
    )

    base_url = f"http://127.0.0.1:{port}"
    session = requests.Session()

    # wait for the server to accept connections (up to 30 s)
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            log_file.close()
            raise RuntimeError(
                f"Controller exited early (rc={proc.returncode}).\n"
                f"Log: {log_path.read_text()[-2000:]}"
            )
        try:
            r = session.get(f"{base_url}/auth/auth/methods", timeout=1)
            if r.status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(0.5)
    else:
        proc.terminate()
        log_file.close()
        raise RuntimeError(
            f"Controller did not start within 30 s.\n"
            f"Log: {log_path.read_text()[-2000:]}"
        )

    # authenticate
    # The controller marks session cookies as Secure for localhost URLs (it treats
    # http://localhost and http://127.0.0.1 as secure contexts, matching browser
    # behaviour). requests enforces the Secure flag strictly and won't resend those
    # cookies over plain HTTP. Work around by reading the raw Set-Cookie headers and
    # re-injecting the cookies without the Secure attribute.
    r = session.post(
        f"{base_url}/auth/login/basic",
        data={"username": "admin", "password": passwd},
        allow_redirects=False,
    )
    assert (
        r.status_code == 303
    ), f"Basic auth login failed: expected 303, got {r.status_code}\n{r.text}"
    for raw_hdr in r.raw.headers.getlist("set-cookie"):
        # parse just the name=value portion (everything before the first ;)
        name_val = raw_hdr.split(";")[0].strip()
        if "=" in name_val:
            name, val = name_val.split("=", 1)
            session.cookies.set(name.strip(), val.strip())

    yield base_url, session, port, tmpdir

    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        # The controller may have a live QEMU child that ignores SIGTERM.
        # Send SIGKILL to the entire process group to guarantee cleanup.
        proc.kill()
        proc.wait()
    log_file.close()
    # Always preserve the log for post-mortem inspection.
    preserved = pathlib.Path("/tmp/thymis-integ-last-run")
    if preserved.exists():
        shutil.rmtree(preserved, ignore_errors=True)
    shutil.copytree(tmpdir, preserved, dirs_exist_ok=True)
    print(f"\n[fixture] controller log preserved at {preserved}/controller.log")
    shutil.rmtree(tmpdir, ignore_errors=True)


# ─────────────────────────────────────────────────────────────────────────────
# test
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.integration
@pytest.mark.timeout(1800)  # 30 min ceiling; individual steps have tighter timeouts
def test_x86_vm_build_start_deploy(controller: ControllerInfo) -> None:
    """
    API-driven equivalent of the Playwright 'Create a x64 vm and run it' test.

    Uses a single VM (api-vm-1) for reliability.  The original Playwright test
    runs two VMs simultaneously; two concurrent nix builds + two QEMU processes
    + two agent log floods saturate the test host and make the deploy step
    unreliable.  Once the single-VM path is stable the test can be extended.

    Steps:
      1. Create one x86-64 VM config via PATCH /api/state
      2. Commit
      3. Trigger build-download-image (image_format=nixos-vm)
      4. Wait for VM to reach 'running' state (build task never reaches
         'completed' while its VM child is alive — do NOT poll for that)
      5. Sleep AGENT_FLOOD_SETTLE_S to let the initial agent log flood drain
      6. Wait for VM to appear in all_connected_deployment_info
      7. Add WhateverModule (custom PS1) + BashModule (jq echo) + secret; commit
      8. Deploy to vm-1
      9. Wait for deploy_device_task to complete  ← the step timing out in CI
     10. SSH into vm-1 to verify custom prompt and bash-service output
    """
    base_url, s, port, project_path = controller

    # ── 1. create VM config ───────────────────────────────────────────────────
    print("\n[step 1] creating VM config")
    state = s.get(f"{base_url}/api/state").json()
    state["configs"] = [
        {
            "displayName": "API VM 1",
            "identifier": "api-vm-1",
            "modules": [
                {
                    "type": MOD_THYMIS_DEVICE,
                    "settings": {
                        "device_type": "generic-x86_64",
                        "image_format": "nixos-vm",
                        "nix_state_version": "25.11",
                    },
                }
            ],
            "tags": [],
        },
    ]
    r = s.patch(f"{base_url}/api/state", json=state)
    assert r.status_code == 200, r.text

    # ── 2. commit ─────────────────────────────────────────────────────────────
    print("[step 2] committing state")
    # Use _commit_until_clean to handle the reload_state background task race:
    # PATCH /api/state returns before reload_state finishes staging host nix files.
    _commit_until_clean(s, base_url, "add test VM")

    # ── 3. trigger build-download-image ───────────────────────────────────────
    print("[step 3] triggering build-download-image for api-vm-1")
    r = s.post(
        f"{base_url}/api/action/build-download-image",
        params={"identifier": "api-vm-1"},
    )
    assert r.status_code == 200, f"build-download-image api-vm-1: {r.text}"

    # ── 4. wait for VM to start ───────────────────────────────────────────────
    # IMPORTANT: build_device_image_task NEVER reaches state "completed" while
    # its child run_nixos_vm_task is alive (executor.py marks parent completed
    # only when it has no children).  Poll run_nixos_vm_task directly instead.
    # also_fail_on catches a failed build early rather than timing out.
    print(
        f"[step 4] waiting for run_nixos_vm_task=running "
        f"(build_device_image_task parent never completes while VM alive)"
    )
    _poll_tasks(
        s,
        base_url,
        type_filter="run_nixos_vm_task",
        target_state="running",
        count=1,
        timeout=720,  # 12 min — nix build can be slow
        poll_interval=15.0,
        also_fail_on=("build_device_image_task",),
    )
    print("[step 4] VM task is running")

    # ── 5. wait for agent log flood to drain ─────────────────────────────────
    # Immediately after the agent connects it sends a burst of 1300+ log
    # batches.  Each POST /agent/logs handler does synchronous SQLAlchemy
    # writes in a for-loop with no await — one batch at a time holds the event
    # loop.  The controller is effectively unresponsive for ~2–5 min.
    # We sleep here so subsequent requests don't hang indefinitely.
    print(
        f"[step 5] sleeping {AGENT_FLOOD_SETTLE_S}s for agent initial log flood to drain"
    )
    time.sleep(AGENT_FLOOD_SETTLE_S)
    print("[step 5] done sleeping")

    # ── 6. confirm VM has connected via the relay ─────────────────────────────
    print("[step 6] waiting for VM to appear in all_connected_deployment_info")
    # Close any stale keep-alive connections left over from before the sleep.
    s.close()
    deadline = time.monotonic() + 120
    connected: list[dict] = []
    while time.monotonic() < deadline:
        try:
            connected = s.get(
                f"{base_url}/api/all_connected_deployment_info",
                timeout=30,
            ).json()
            if connected:
                break
        except requests.RequestException as exc:
            print(f"  [step 6] request error: {exc} — retrying")
        time.sleep(5)
    assert len(connected) >= 1, (
        f"No VMs connected after {AGENT_FLOOD_SETTLE_S + 120}s.\n"
        f"Connected: {connected}"
    )

    conn_by_config = {c["deployed_config_id"]: c["id"] for c in connected}
    assert (
        "api-vm-1" in conn_by_config
    ), f"api-vm-1 not in connected deployment infos: {list(conn_by_config)}"
    print(f"[step 6] VM connected: deployment_info_id={conn_by_config['api-vm-1']}")

    # ── 7. add modules and secret to api-vm-1; commit ────────────────────────
    print("[step 7] adding modules, secret, and committing")
    r = s.post(
        f"{base_url}/api/secrets",
        json={
            "display_name": "secret.txt",
            "type": "single_line",
            "value_str": "THIS IS A SECRET",
            "filename": "secret.txt",
            "include_in_image": False,
        },
    )
    assert r.status_code == 200, r.text
    secret_id: str = r.json()["id"]

    state = s.get(f"{base_url}/api/state").json()
    for cfg in state["configs"]:
        if cfg["identifier"] != "api-vm-1":
            continue
        # attach secret to the core device module
        for mod in cfg["modules"]:
            if mod["type"] == MOD_THYMIS_DEVICE:
                mod["settings"]["secrets"] = [
                    {
                        "secret": secret_id,
                        "path": "/run/thymis/secret.txt",
                        "owner": "root",
                        "group": "root",
                        "mode": "0600",
                    }
                ]
        # custom NixOS settings: inject secret into PS1
        cfg["modules"].append(
            {
                "type": MOD_WHATEVER,
                "settings": {
                    "settings": (
                        'programs.bash.promptInit = "PS1=\\"\\[`cat /run/thymis/secret.txt`'
                        'Hello World Custom Prompt\\] \\"";'
                        'services.openssh.settings.PrintLastLog = "no";'
                    )
                },
            }
        )
        # bash service: echo json through jq
        cfg["modules"].append(
            {
                "type": MOD_BASH,
                "settings": {
                    "script": 'echo \'{"key": "value"}\' | jq "."',
                    "packages": [{"package": "jq"}],
                    "timer_config": {
                        "type": "systemd-timer",
                        "timer_type": "monotonic",
                        "on_boot_sec": "1s",
                        "accuracy_sec": "1s",
                    },
                },
            }
        )
        break

    r = s.patch(f"{base_url}/api/state", json=state)
    assert r.status_code == 200, r.text

    _commit_until_clean(s, base_url, "add modules and secret to api-vm-1")
    print("[step 7] committed")

    # Print the project tmpdir so we can SSH in live during the deploy.
    print(f"[debug] project_path={project_path}  → ssh key: {project_path}/id_thymis")
    # ── 8. deploy to vm-1 ────────────────────────────────────────────────────
    print("[step 8] triggering deploy for api-vm-1")
    r = s.post(
        f"{base_url}/api/action/deploy",
        params={"config": ["api-vm-1"]},
    )
    assert r.status_code == 200, r.text

    # ── 9. wait for the deploy task to complete ───────────────────────────────
    #
    # This is the step that times out in the Playwright CI run (line 201 of
    # x86_vm.spec.ts).  Here, if the task fails the error message and stdout/
    # stderr are included in the assertion, making the root cause immediately
    # visible without needing to download trace ZIPs.
    print("[step 9] waiting for deploy_device_task to complete (timeout 720s)")
    try:
        _poll_tasks(
            s,
            base_url,
            type_filter="deploy_device_task",
            target_state="completed",
            count=1,
            timeout=720,
            poll_interval=15.0,
            also_fail_on=("deploy_devices_task",),
        )
    except (AssertionError, TimeoutError):
        # Dump full task list and tail of controller log for diagnosis.
        try:
            tasks = s.get(
                f"{base_url}/api/tasks", params={"limit": 200}, timeout=30
            ).json()
            print("\n[debug] ALL TASKS at failure:")
            for t in tasks:
                print(f"  {t['task_type']:40s} {t['state']:12s} ", end="")
                if t.get("exception"):
                    print(f"exception={t['exception']!r}")
                else:
                    print()
                if t.get("process_stdout"):
                    print(f"    stdout: {t['process_stdout'][-2000:]}")
                if t.get("process_stderr"):
                    print(f"    stderr: {t['process_stderr'][-2000:]}")
        except Exception as dump_exc:
            print(f"[debug] task dump failed: {dump_exc}")
        try:
            log = (project_path / "controller.log").read_text()
            print("\n[debug] CONTROLLER LOG (last 200 lines):")
            for line in log.splitlines()[-200:]:
                print(f"  {line}")
        except Exception as log_exc:
            print(f"[debug] log read failed: {log_exc}")
        raise
    print("[step 9] deploy completed successfully")

    # ── 10. SSH verification ──────────────────────────────────────────────────
    print("[step 10] verifying deployment via SSH")
    di_id = conn_by_config["api-vm-1"]
    r = s.post(f"{base_url}/api/access_client_token/{di_id}")
    assert r.status_code == 200, r.text
    token = r.json()["token"]

    relay_ws = f"ws://127.0.0.1:{port}/agent/relay_for_clients"
    key_path = str(project_path / "id_thymis")

    def _ssh(command: str, timeout: int = 30) -> str:
        result = subprocess.run(
            [
                "ssh",
                "-i",
                key_path,
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=10",
                "-o",
                (
                    f"ProxyCommand=access-client"
                    f" --relay-url {relay_ws}"
                    f" --secret {token}"
                    f" {di_id} localhost %p tcp"
                ),
                "root@localhost",
                command,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout + result.stderr

    # verify secret was injected into the prompt
    ps1_out = _ssh("echo $PS1")
    print(f"[step 10] $PS1 output: {ps1_out!r}")
    assert (
        "THIS IS A SECRET" in ps1_out or "Hello World Custom Prompt" in ps1_out
    ), f"Expected custom prompt in $PS1 output, got: {ps1_out!r}"

    # verify the bash service ran and produced jq output
    journal_out = _ssh(
        "journalctl -u thymis-bash-service-hosts-api-vm-1.service -o cat --no-pager"
    )
    print(f"[step 10] journal output: {journal_out!r}")
    assert (
        '"key": "value"' in journal_out
    ), f"Expected jq output in bash service journal, got: {journal_out!r}"

    print("[step 10] SSH verification passed")
