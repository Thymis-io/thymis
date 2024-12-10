import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.connection import Connection, Pipe

from thymis_controller.models import task as task_models


class TaskWorkerPoolManager:
    def __init__(self):
        self.pool = ProcessPoolExecutor()
        self.futures = {}

    def submit(self, task_submission: task_models.TaskSubmission):
        child_in, child_out = Pipe()
        future = self.pool.submit(
            worker_run_task, task_submission, (child_in, child_out)
        )
        self.futures[task_submission.id] = (future, child_in, child_out)

    async def start(self):
        pass

    def stop(self):
        concurrent.futures.wait((f for f, _, _ in self.futures.values()))


def worker_run_task(task: task_models.Task, conn: (Connection, Connection)):
    pass
