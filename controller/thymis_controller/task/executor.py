import concurrent.futures
import contextlib
import logging
import threading
from concurrent.futures import Future, ProcessPoolExecutor
from multiprocessing.connection import Connection, Pipe

import sqlalchemy.orm
import thymis_controller.crud.task as crud_task
import thymis_controller.models.task as models_task
from thymis_controller.database.connection import create_sqlalchemy_engine
from thymis_controller.task.worker import worker_run_task

logger = logging.getLogger(__name__)


class TaskWorkerPoolManager:
    def __init__(self):
        self.pool = ProcessPoolExecutor()
        self.futures = {}
        self.future_to_id = {}
        self.listen_threads = {}

    def submit(self, task_submission: models_task.TaskSubmission):
        worker_side, executor_side = Pipe()
        future = self.pool.submit(worker_run_task, task_submission, (worker_side))
        future.add_done_callback(self.finish_task)
        self.futures[task_submission.id] = (future, worker_side, executor_side)
        self.future_to_id[future] = task_submission.id
        thread = threading.Thread(
            target=self.listen_child_messages, args=(executor_side,)
        )
        thread.start()
        self.listen_threads[task_submission.id] = thread

    @contextlib.asynccontextmanager
    async def start(self):
        engine = create_sqlalchemy_engine()

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

    def listen_child_messages(self, conn: Connection):
        while True:
            try:
                conn.recv()
                # logger.info("Received message from worker: %s", message)
            except EOFError:
                # logger.info("Worker connection closed")
                break

    def finish_task(self, future: Future):
        task_id = self.future_to_id[future]
        future, child_in, child_out = self.futures.pop(task_id)
        logger.info("Task %s worker finished execution", task_id)
