import base64
import datetime
import glob
import json
import os
import pathlib
import platform
import queue
import random
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from multiprocessing.connection import Connection
from typing import IO, AnyStr, List, assert_never

import thymis_controller.models.task as models_task
from thymis_controller.nix import NIX_CMD
from thymis_controller.nix.log_parse import NixParser


class ProcessList:
    def __init__(self):
        self.processes: list[subprocess.Popen[bytes]] = []
        self.terminated = False
        self._lock = threading.Lock()
        self.msg_queue = queue.Queue()

    def add(self, process: subprocess.Popen[bytes]):
        with self._lock:
            self.processes.append(process)
        if self.terminated:
            process.terminate()

    def terminate_all(self):
        self.terminated = True
        with self._lock:
            for process in self.processes:
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.terminate()

    def kill_all(self):
        with self._lock:
            for process in self.processes:
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    process.kill()


def listen_for_executor(conn: Connection, process_list: ProcessList):
    while not conn.closed:
        try:
            message = conn.recv()
            if not isinstance(message, models_task.ControllerToRunnerTaskUpdate):
                print("Received unexpected message type %s", type(message))
                continue
            match message.inner:
                case models_task.CancelTask():
                    process_list.terminate_all()
                    time.sleep(1)
                    process_list.kill_all()
                case models_task.AgentSwitchToNewConfigurationResult():
                    process_list.msg_queue.put(message)
                case _:
                    print("Received unexpected message %s", message)
                    assert_never(message)
        except EOFError:
            break
        except OSError:
            break


def worker_run_task(task: models_task.TaskSubmission, conn: Connection):
    process_list = ProcessList()
    executor_thread = threading.Thread(
        target=listen_for_executor, args=(conn, process_list)
    )
    executor_thread.start()

    if task.data.type not in SUPPORTED_TASK_TYPES:
        reject_task(f"Task type {task.data.type} not supported", task, conn)
        conn.close()
        return
    pick_task(task, conn)
    try:
        SUPPORTED_TASK_TYPES[task.data.type](task, conn, process_list)
    except Exception as e:
        report_task_finished(task, conn, False, f"Exception: {e}")

    conn.close()
    executor_thread.join()


def pick_task(task: models_task.TaskSubmission, conn: Connection):
    conn.send(
        models_task.RunnerToControllerTaskUpdate(
            id=task.id,
            update=models_task.TaskPickedUpdate(),
        )
    )
    print("Task picked")


def reject_task(reason: str, task: models_task.TaskSubmission, conn: Connection):
    conn.send(
        models_task.RunnerToControllerTaskUpdate(
            id=task.id, update=models_task.TaskRejectedUpdate(reason=reason)
        )
    )


def project_flake_update_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "project_flake_update_task"
    repo_path = (pathlib.Path(task_data.project_path) / "repository").resolve()

    # runs `nix flake update` in the project directory
    returncode = run_command(
        task,
        conn,
        process_list,
        [*NIX_CMD, "flake", "update"],
        cwd=repo_path,
    )
    if returncode == 0:
        report_task_finished(task, conn)
    else:
        report_task_finished(task, conn, False, "Flake update failed")


def build_project_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "build_project_task"
    repo_path = (pathlib.Path(task_data.project_path) / "repository").resolve()

    # runs `nix build` in the project directory
    returncode = run_command(
        task,
        conn,
        process_list,
        [
            *NIX_CMD,
            "build",
            ".#thymis",
            "--out-link",
            "/tmp/thymis",
        ],
        cwd=repo_path,
    )
    if returncode == 0:
        report_task_finished(task, conn)
    else:
        report_task_finished(task, conn, False, "Build failed")


def deploy_device_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "deploy_device_task"
    repo_path = (pathlib.Path(task_data.project_path) / "repository").resolve()

    # first print verison of `nix` and `nix-copy-closure`

    with tempfile.TemporaryDirectory() as tmpdir:
        # write deployment_public_key to tmpfile
        hostfile_path = f"{tmpdir}/known_hosts"
        with open(hostfile_path, "w", encoding="utf-8") as hostfile:
            hostfile.write(f"localhost {task_data.device.deployment_public_key}\n")
            hostfile.flush()
        env = {
            "NIX_SSHOPTS": f"-i {task_data.ssh_key_path} "
            f"-o UserKnownHostsFile={hostfile.name} "
            f"-o StrictHostKeyChecking=yes "
            f"-o PasswordAuthentication=no "
            f"-o KbdInteractiveAuthentication=no "
            f"-o ConnectTimeout=10 "
            f"-o BatchMode=yes "
            f"-o 'ProxyCommand {(os.getenv('PYTHONENV')+'/bin/python') if ('PYTHONENV' in os.environ) else 'python' } -m thymis_controller.access_client {task_data.controller_access_client_endpoint} {task_data.device.deployment_info_id}' "
            "-T",
            "PATH": os.getenv("PATH"),
            "HTTP_NETWORK_RELAY_SECRET": task_data.access_client_token,
            **(
                {"DBUS_SESSION_BUS_ADDRESS": os.getenv("DBUS_SESSION_BUS_ADDRESS")}
                if "DBUS_SESSION_BUS_ADDRESS" in os.environ
                else {}
            ),
        }
        toplevel_path = f"{tmpdir}/toplevel"
        returncode = run_command(
            task,
            conn,
            process_list,
            [
                *NIX_CMD,
                "build",
                f'{repo_path}#nixosConfigurations."{task_data.device.identifier}".config.system.build.toplevel',
                "--out-link",
                toplevel_path,
            ],
            env,
            cwd=tmpdir,
        )

        if returncode != 0:
            report_task_finished(task, conn, False, "Build failed")
            return

        # resolve the toplevel path
        config_path = str(pathlib.Path(toplevel_path).resolve())

        returncode = run_command(
            task,
            conn,
            process_list,
            [
                "systemd-run",
                "-E",
                "NIX_SSHOPTS",
                "-E",
                "HTTP_NETWORK_RELAY_SECRET",
                "-E",
                "PATH",
                *(["--user"] if "DBUS_SESSION_BUS_ADDRESS" in os.environ else []),
                "--collect",
                "--no-ask-password",
                "--pipe",
                "--quiet",
                "--service-type=exec",
                f"--unit=thymis-nix-copy-closure-{random.randbytes(8).hex()}",
                "--wait",
                "nix-copy-closure",
                *NIX_CMD[1:],
                "--to",
                "root@localhost",
                config_path,
            ],
            env,
            cwd=tmpdir,
        )

        if returncode != 0:
            report_task_finished(task, conn, False, "Copy closure failed")
            return

        # send message to agent on device that it should switch to the new configuration
        conn.send(
            models_task.RunnerToControllerTaskUpdate(
                id=task.id,
                update=models_task.AgentShouldSwitchToNewConfigurationUpdate(
                    deployment_info_id=task_data.device.deployment_info_id,
                    path_to_configuration=config_path,
                ),
            )
        )

        # wait for agent to switch to new configuration
        try:
            message = process_list.msg_queue.get(timeout=300)
            if not isinstance(
                message.inner, models_task.AgentSwitchToNewConfigurationResult
            ):
                report_task_finished(task, conn, False, "Unexpected message from agent")
                return
        except queue.Empty:
            report_task_finished(task, conn, False, "Timeout waiting for agent")
        except Exception as e:
            report_task_finished(task, conn, False, f"Exception: {e}")
        else:
            if message.inner.success:
                report_task_finished(task, conn)
            else:
                report_task_finished(task, conn, False, "Agent failed to switch")


def deploy_devices_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "deploy_devices_task"

    report_task_finished(task, conn, True, "Waiting for child tasks to finish")


def build_device_image_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "build_device_image_task"
    project_path = pathlib.Path(task_data.project_path).resolve()
    repo_path = (pathlib.Path(task_data.project_path) / "repository").resolve()

    device_module = next(
        (
            module
            for module in task_data.device_state.get("modules", [])
            if module.get("type") == "thymis_controller.modules.thymis.ThymisDevice"
        ),
        None,
    )
    if device_module is None:
        report_task_finished(task, conn, False, "Device module not found")
        return
    image_format = device_module.get("settings", {}).get("image_format")
    if image_format is None:
        report_task_finished(task, conn, False, "Image format not found")
        return

    secrets_builder_dest = f"{task_data.project_path}/image-builders/{task_data.configuration_id}.secrets-builder"
    final_image_dest_base = (
        f"{task_data.project_path}/images/{task_data.configuration_id}"
    )
    # create dirs
    os.makedirs(project_path / "image-builders", exist_ok=True)
    os.makedirs(project_path / "images", exist_ok=True)

    architectures = ["x86_64", "aarch64"]
    architecture = None
    for arch in architectures:
        if arch in platform.machine():
            architecture = arch
            break
    if architecture is None:
        report_task_finished(task, conn, False, "Unsupported build host architecture")
        return

    returncode = run_command(
        task,
        conn,
        process_list,
        [
            *NIX_CMD,
            "build",
            f'git+file:{repo_path}?rev={task_data.commit}#nixosConfigurations."{task_data.configuration_id}".config.system.build.thymis-image-with-secrets-builder-{architecture}',
            "--out-link",
            secrets_builder_dest,
        ],
        cwd=repo_path,
    )

    if returncode != 0:
        report_task_finished(task, conn, False, "Build failed")
        return

    with tempfile.TemporaryDirectory() as tmpdir:
        token = f"thymis-{random.randbytes(64).hex()}"  # see agent/thymis_agent/agent.py `AGENT_TOKEN_EXPECTED_FORMAT =`
        with open(f"{tmpdir}/thymis-token.txt", "w", encoding="utf-8") as f:
            f.write(token)
        with open(f"{tmpdir}/thymis-metadata.json", "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "configuration_id": task_data.configuration_id,
                        "configuration_commit": task_data.commit,
                        "datetime": str(datetime.datetime.now()),
                    }
                )
            )
        with open(
            f"{tmpdir}/thymis-controller-ssh-pubkey.txt", "w", encoding="utf-8"
        ) as f:
            f.write(task_data.controller_ssh_pubkey)

        # delete all old files in final_image_dest_base*
        for file in glob.glob(f"{final_image_dest_base}*"):
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
        returncode = run_command(
            task,
            conn,
            process_list,
            [secrets_builder_dest, tmpdir, final_image_dest_base],
            cwd=repo_path,
        )
        if returncode != 0:
            report_task_finished(task, conn, False, "Image secrets builder failed")
            return

        conn.send(
            models_task.RunnerToControllerTaskUpdate(
                id=task.id,
                update=models_task.ImageBuiltUpdate(
                    configuration_id=task_data.configuration_id,
                    configuration_commit=task_data.commit,
                    image_format=image_format,
                    token=token,
                ),
            )
        )

    if not glob.glob(f"{final_image_dest_base}*"):
        report_task_finished(
            task, conn, False, "Image build failed, no image found at destination"
        )

    report_task_finished(task, conn)


def run_nixos_vm_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "run_nixos_vm_task"
    project_path = pathlib.Path(task_data.project_path).resolve()

    with tempfile.TemporaryDirectory() as tmpdir:
        returncode = run_command(
            task,
            conn,
            process_list,
            [
                f"{project_path}/images/{task_data.configuration_id}.start-vm",
                "-display",
                "none",
                "-vnc",
                "localhost:0,to=99",
            ],
            cwd=tmpdir,
        )

    if returncode == 0:
        report_task_finished(task, conn)
    else:
        report_task_finished(task, conn, False, "VM run failed")


def ssh_command_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "ssh_command_task"

    returncode = run_command(
        task,
        conn,
        process_list,
        [
            "ssh",
            f"-o UserKnownHostsFile={task_data.ssh_known_hosts_path}",
            "-o StrictHostKeyChecking=yes",
            "-o ConnectTimeout=10",
            f"-i {task_data.ssh_key_path}",
            f"-p {task_data.target_port}",
            f"{task_data.target_user}@{task_data.target_host}",
            task_data.command,
        ],
    )

    if returncode == 0:
        report_task_finished(task, conn)
    else:
        report_task_finished(task, conn, False, "SSH command failed")


SUPPORTED_TASK_TYPES = {
    "project_flake_update_task": project_flake_update_task,
    "build_project_task": build_project_task,
    "deploy_devices_task": deploy_devices_task,
    "deploy_device_task": deploy_device_task,
    "build_device_image_task": build_device_image_task,
    "ssh_command_task": ssh_command_task,
    "run_nixos_vm_task": run_nixos_vm_task,
}


def run_command(
    task: models_task.TaskSubmission,
    conn: Connection,
    process_list: ProcessList,
    args: List[str],
    env: dict = None,
    cwd: str = None,
    input: AnyStr = None,
):
    if process_list.terminated:
        return -1

    conn.send(
        models_task.RunnerToControllerTaskUpdate(
            id=task.id,
            update=models_task.CommandRunUpdate(args=args, env=env, cwd=str(cwd)),
        )
    )

    proc = subprocess.Popen(
        args,
        env=env,
        cwd=cwd,
        stdin=(subprocess.PIPE if input else None),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        process_group=0,
    )

    process_list.add(proc)

    buffer_lock = threading.Lock()
    stdout_buffer = bytearray()
    stderr_buffer = bytearray()

    stdout_thread = threading.Thread(
        target=stream_to_buffer, args=(proc.stdout, stdout_buffer, buffer_lock)
    )
    stderr_thread = threading.Thread(
        target=stream_to_buffer, args=(proc.stderr, stderr_buffer, buffer_lock)
    )

    nix_parser = NixParser()

    # another thread for regularly sending updates to the controller (every second?)
    # this thread should also clear the buffers after sending
    def flush_buffers():
        nonlocal stdout_buffer
        nonlocal stderr_buffer
        if stdout_buffer or stderr_buffer:
            with buffer_lock:
                stdout = stdout_buffer.copy()
                stdout_buffer.clear()
                if proc.poll() is None:
                    stderr = nix_parser.take_complete_lines(stderr_buffer)
                else:
                    stderr = stderr_buffer.copy()
                    stderr_buffer.clear()

            has_processed_nix_lines = nix_parser.process_buffer(stderr)
            if has_processed_nix_lines:
                conn.send(
                    models_task.RunnerToControllerTaskUpdate(
                        id=task.id,
                        update=models_task.TaskNixStatusUpdate(
                            status=nix_parser.get_model()
                        ),
                    )
                )
            if stdout or stderr:
                conn.send(
                    models_task.RunnerToControllerTaskUpdate(
                        id=task.id,
                        update=models_task.TaskStdOutErrUpdate(
                            stdoutb64=base64.b64encode(stdout).decode("utf-8"),
                            stderrb64=base64.b64encode(stderr).decode("utf-8"),
                        ),
                    )
                )

    def send_update():
        while stdout_buffer or stderr_buffer or (proc.poll() is None):
            flush_buffers()
            time.sleep(0.5)

    update_thread = threading.Thread(target=send_update)

    stdout_thread.start()
    stderr_thread.start()
    update_thread.start()

    if input:
        proc.stdin.write(input)
        proc.stdin.close()

    open_fds = [proc.stdout, proc.stderr]
    while open_fds:
        copy_fds = open_fds.copy()
        for fd in copy_fds:
            if fd.closed:
                open_fds.remove(fd)
        time.sleep(0.5)

    proc.wait()
    stdout_thread.join(0.5)
    stderr_thread.join(0.5)
    update_thread.join(1.5)

    # if anything is still alive, complain
    if proc.poll() is None:
        raise RuntimeError("Process did not stop properly")
    if stdout_thread.is_alive() or stderr_thread.is_alive() or update_thread.is_alive():
        # raise RuntimeError("Threads did not stop properly")
        if stdout_thread.is_alive():
            raise RuntimeError("stdout_thread did not stop properly")
        if stderr_thread.is_alive():
            raise RuntimeError("stderr_thread did not stop properly")
        if update_thread.is_alive():
            raise RuntimeError("update_thread did not stop properly")

    return proc.returncode


def report_task_finished(task, conn, success=True, reason=None):
    if success:
        conn.send(
            models_task.RunnerToControllerTaskUpdate(
                id=task.id,
                update=models_task.TaskCompletedUpdate(),
            )
        )
    else:
        conn.send(
            models_task.RunnerToControllerTaskUpdate(
                id=task.id,
                update=models_task.TaskFailedUpdate(reason=reason),
            )
        )


def stream_to_buffer(stream: IO[bytes], buffer: bytearray, lock: threading.Lock):
    while True:
        data = stream.read(1024)
        if not data:
            break
        with lock:
            buffer += data
    stream.close()
