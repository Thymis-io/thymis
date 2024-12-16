from multiprocessing.connection import Connection

import thymis_controller.models.task as models_task


def worker_run_task(task: models_task.TaskSubmission, conn: (Connection, Connection)):
    print(f"Running task {task.id}")
