import base64
import pathlib
import subprocess
import threading
import time
from multiprocessing.connection import Connection
from typing import AnyStr, List

import thymis_controller.models.task as models_task


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


SUPPORTED_TASK_TYPES = {"project_flake_update_task": project_flake_update_task}


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

    stdout_buffer = b""
    stderr_buffer = b""
    stdout_thread = threading.Thread(
        target=stream_to_buffer, args=(proc.stdout, stdout_buffer)
    )
    stderr_thread = threading.Thread(
        target=stream_to_buffer, args=(proc.stderr, stderr_buffer)
    )

    # another thread for regularly sending updates to the controller (every second?)
    # this thread should also clear the buffers after sending
    def send_update():
        nonlocal stdout_buffer
        nonlocal stderr_buffer
        while proc.poll() is None:
            conn.send(
                models_task.RunnerToControllerTaskUpdate(
                    id=task.id,
                    update=models_task.TaskStdOutErrUpdate(
                        stdoutb64=base64.b64encode(stdout_buffer).decode("utf-8"),
                        stderrb64=base64.b64encode(stderr_buffer).decode("utf-8"),
                    ),
                )
            )
            stdout_buffer = b""
            stderr_buffer = b""
            time.sleep(1)

    update_thread = threading.Thread(target=send_update)

    stdout_thread.start()
    stderr_thread.start()
    update_thread.start()

    if input:
        proc.stdin.write(input)
        proc.stdin.close()

    proc.wait()
    stdout_thread.join()
    stderr_thread.join()
    update_thread.join()

    conn.send(
        models_task.RunnerToControllerTaskUpdate(
            id=task.id,
            update=models_task.TaskCompletedUpdate(),
        )
    )


def stream_to_buffer(stream, buffer):
    for line in stream:
        buffer += line
