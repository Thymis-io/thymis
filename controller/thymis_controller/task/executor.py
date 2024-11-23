import concurrent
from multiprocessing.connection import Connection, Pipe

from thymis_controller.models import task as task_models


class TaskWorkerPoolManager:
    def __init__(self):
        self.pool = concurrent.futures.ProcessPoolExecutor()

    def submit(self, task: task_models.Task):
        child_in, child_out = Pipe()
        self.pool.submit(worker_run_task, task, (child_in, child_out))

        raise NotImplementedError("Implement me!")


def worker_run_task(task: task_models.Task, conn: (Connection, Connection)):
    raise NotImplementedError("Implement me!")
