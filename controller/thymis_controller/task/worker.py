import base64
import os
import pathlib
import signal
import subprocess
import threading
import time
from multiprocessing.connection import Connection
from typing import IO, AnyStr, List

import thymis_controller.models.task as models_task
from thymis_controller.nix import NIX_CMD
from thymis_controller.nix.log_parse import NixParser


class ProcessList:
    def __init__(self):
        self.processes: list[subprocess.Popen[bytes]] = []
        self.terminated = False
        self._lock = threading.Lock()

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
            if isinstance(message, models_task.CancelTask):
                process_list.terminate_all()
                time.sleep(1)
                process_list.kill_all()
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
    project_path = pathlib.Path(task_data.project_path).resolve()

    # runs `nix flake update` in the project directory
    returncode = run_command(
        task,
        conn,
        process_list,
        [*NIX_CMD, "flake", "update"],
        cwd=project_path,
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
    project_path = pathlib.Path(task_data.project_path).resolve()

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
        cwd=project_path,
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
    project_path = pathlib.Path(task_data.project_path).resolve()

    returncode = run_command(
        task,
        conn,
        process_list,
        [
            "nixos-rebuild",
            *NIX_CMD[1:],
            "switch",
            "--flake",
            f"{project_path}#{task_data.device.identifier}",
            "--target-host",
            f"{task_data.device.username}@{task_data.device.host}",
        ],
        {
            "NIX_SSHOPTS": f"-i {task_data.ssh_key_path} -p {task_data.device.port} -o UserKnownHostsFile={task_data.known_hosts_path} -o StrictHostKeyChecking=yes -o PasswordAuthentication=no -o KbdInteractiveAuthentication=no -o ConnectTimeout=10",
            "PATH": os.getenv("PATH"),
        },
        cwd=project_path,
    )

    if returncode == 0:
        report_task_finished(task, conn)
    else:
        report_task_finished(task, conn, False, "Deploy failed")


def deploy_devices_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "deploy_devices_task"


def build_device_image_task(
    task: models_task.TaskSubmission, conn: Connection, process_list: ProcessList
):
    task_data = task.data
    assert task_data.type == "build_device_image_task"
    project_path = pathlib.Path(task_data.project_path).resolve()

    returncode = run_command(
        task,
        conn,
        process_list,
        [
            *NIX_CMD,
            "build",
            f'.#nixosConfigurations."{task_data.device_identifier}".config.system.build.thymis-image',
            "--out-link",
            f"/tmp/thymis-devices.{task_data.device_identifier}",
        ],
        cwd=project_path,
    )

    if returncode == 0:
        report_task_finished(task, conn)
    else:
        report_task_finished(task, conn, False, "Build failed")


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
                stderr = nix_parser.take_complete_lines(stderr_buffer)

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
