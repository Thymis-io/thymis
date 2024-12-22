import base64
import pathlib
import subprocess
import threading
import time
from multiprocessing.connection import Connection
from typing import IO, AnyStr, List

import thymis_controller.models.task as models_task
from thymis_controller.nix.log_parse import NixParser


def worker_run_task(task: models_task.TaskSubmission, conn: Connection):
    if task.data.type not in SUPPORTED_TASK_TYPES:
        reject_task(f"Task type {task.data.type} not supported", task, conn)
        return
    pick_task(task, conn)
    try:
        SUPPORTED_TASK_TYPES[task.data.type](task, conn)
    except Exception as e:
        conn.send(
            models_task.RunnerToControllerTaskUpdate(
                id=task.id,
                update=models_task.TaskFailedUpdate(reason=f"Exception: {e}"),
            )
        )
    conn.close()


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


def project_flake_update_task(task: models_task.TaskSubmission, conn: Connection):
    task_data = task.data
    assert task_data.type == "project_flake_update_task"
    project_path = pathlib.Path(task_data.project_path).resolve()

    # runs `nix flake update` in the project directory
    run_command(
        task,
        conn,
        ["nix", "flake", "update"],
        cwd=project_path,
    )
    report_task_finished(task, conn)


def build_project_task(task: models_task.TaskSubmission, conn: Connection):
    task_data = task.data
    assert task_data.type == "build_project_task"
    project_path = pathlib.Path(task_data.project_path).resolve()

    # runs `nix build` in the project directory
    run_command(
        task,
        conn,
        [
            "nix",
            "build",
            ".#thymis",
            "--out-link",
            "/tmp/thymis",
            "--log-format",
            "internal-json",
        ],
        cwd=project_path,
    )
    report_task_finished(task, conn)


def test_task(task: models_task.TaskSubmission, conn: Connection):
    print("Running test task")
    run_command(
        task,
        conn,
        ["echo", "Hello, world!"],
    )
    for i in range(10):
        run_command(
            task,
            conn,
            ["sleep", "1"],
        )
        run_command(
            task,
            conn,
            ["echo", "Hello, world!", str(i)],
        )
    report_task_finished(task, conn)


SUPPORTED_TASK_TYPES = {
    "project_flake_update_task": project_flake_update_task,
    "build_project_task": build_project_task,
    "test_task": test_task,
}


def run_command(
    task: models_task.TaskSubmission,
    conn: Connection,
    args: List[str],
    env: dict = None,
    cwd: str = None,
    input: AnyStr = None,
):
    proc = subprocess.Popen(
        args,
        env=env,
        cwd=cwd,
        stdin=(subprocess.PIPE if input else None),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

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


def report_task_finished(task, conn):
    conn.send(
        models_task.RunnerToControllerTaskUpdate(
            id=task.id,
            update=models_task.TaskCompletedUpdate(),
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
