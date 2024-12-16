from multiprocessing.connection import Connection

import thymis_controller.models.task as models_task


def worker_run_task(task: models_task.TaskSubmission, conn: Connection):
    if task.data.type not in []:
        reject_task(f"Task type {task.data.type} not supported", task, conn)
    pick_task(task, conn)


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
