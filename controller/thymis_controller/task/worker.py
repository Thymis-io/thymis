from multiprocessing.connection import Connection

import thymis_controller.models.task as models_task


def worker_run_task(task: models_task.TaskSubmission, conn: Connection):
    if task.data.type not in SUPPORTED_TASK_TYPES:
        reject_task(f"Task type {task.data.type} not supported", task, conn)
        return
    pick_task(task, conn)
    SUPPORTED_TASK_TYPES[task.data.type](task, conn)


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


def project_flake_update_task():
    pass


SUPPORTED_TASK_TYPES = {"project_flake_update_task": project_flake_update_task}
