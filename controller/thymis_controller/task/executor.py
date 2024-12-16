import concurrent.futures
import contextlib
import logging
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.connection import Pipe

import sqlalchemy.orm
import thymis_controller.crud.task as crud_task
import thymis_controller.models.task as models_task
from thymis_controller.task.worker import worker_run_task

logger = logging.getLogger(__name__)


class TaskWorkerPoolManager:
    def __init__(self):
        self.pool = ProcessPoolExecutor()
        self.futures = {}

    def submit(self, task_submission: models_task.TaskSubmission):
        child_in, child_out = Pipe()
        future = self.pool.submit(
            worker_run_task, task_submission, (child_in, child_out)
        )
        self.futures[task_submission.id] = (future, child_in, child_out)

    @contextlib.asynccontextmanager
    async def start(self):
        from thymis_controller.database.connection import (
            engine,  # pylint: disable=import-outside-toplevel
        )

        with sqlalchemy.orm.Session(engine) as db_session:
            amount_running_when_shut_down = crud_task.fail_running_tasks(db_session)
            logger.info(
                "Failed %d tasks that were running when the controller shut down",
                amount_running_when_shut_down,
            )
            pending_tasks = crud_task.get_pending_tasks(db_session)
            for task in pending_tasks:
                self.submit(models_task.TaskSubmission.from_orm(task))
            yield self
        self.stop()

    def stop(self):
        concurrent.futures.wait((f for f, _, _ in self.futures.values()))
        self.pool.shutdown()
