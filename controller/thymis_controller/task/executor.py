import concurrent.futures
import logging
import threading
import time
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from multiprocessing.connection import Connection, Pipe

import sqlalchemy.orm
import thymis_controller.crud.task as crud_task
import thymis_controller.models.task as models_task
from thymis_controller.task.subscribe_ui import TaskUISubscriptionManager
from thymis_controller.task.worker import worker_run_task

logger = logging.getLogger(__name__)


class TaskWorkerPoolManager:
    def __init__(self):
        self.pool = ProcessPoolExecutor()
        self.futures = {}
        self.future_to_id = {}
        self.listen_threads = {}
        self._db_engine = None
        self._ui_subscription_manager = None

    @property
    def db_engine(self):
        if self._db_engine is None:
            raise ValueError("TaskWorkerPoolManager not started")
        return self._db_engine

    @property
    def ui_subscription_manager(self) -> "TaskUISubscriptionManager":
        if self._ui_subscription_manager is None:
            raise ValueError(
                "TaskWorkerPoolManager does not have a UI subscription manager"
            )
        return self._ui_subscription_manager

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

    async def start(self, db_engine: sqlalchemy.Engine):
        self._db_engine = db_engine

        with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
            amount_running_when_shut_down = crud_task.fail_running_tasks(db_session)
            logger.info(
                "Failed %d tasks that were running when the controller shut down",
                amount_running_when_shut_down,
            )
            pending_tasks = crud_task.get_pending_tasks(db_session)
            for task in pending_tasks:
                self.submit(models_task.TaskSubmission.from_orm_task(task))
            logger.info(
                "TaskWorkerPoolManager started, %d pending tasks submitted",
                len(pending_tasks),
            )

    def stop(self):
        concurrent.futures.wait((f for f, _, _ in self.futures.values()))
        self.pool.shutdown()
        for thread in self.listen_threads.values():
            thread.join()

    def listen_child_messages(self, conn: Connection):
        while True:
            try:
                message = conn.recv()
                with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                    if not isinstance(
                        message, models_task.RunnerToControllerTaskUpdate
                    ):
                        logger.error(
                            "Received invalid message from worker: %s", message
                        )
                        continue
                    task = crud_task.get_task_by_id(db_session, message.id)
                    if task is None:
                        logger.error("Received message for unknown task: %s", message)
                        continue
                    if isinstance(message.update, models_task.TaskPickedUpdate):
                        task.state = "running"
                        db_session.commit()
                    elif isinstance(message.update, models_task.TaskRejectedUpdate):
                        task.state = "failed"
                        task.exception = f"Task rejected: {message.update.reason}"
                        task.end_time = datetime.now()
                        db_session.commit()
                    else:
                        logger.error(
                            "Received invalid message from worker: %s", message
                        )
                    # notify UI
                    self.ui_subscription_manager.notify_task_update(task)
                    logger.info("Received message from worker: %s", message)
            except EOFError:
                # logger.info("Worker connection closed")
                break

    def finish_task(self, future: Future):
        task_id = self.future_to_id[future]
        future, child_in, child_out = self.futures.pop(task_id)
        logger.info("Task %s worker finished execution", task_id)
        # if task is still running in the database, mark it as failed due to worker finishing before signalling success
        time.sleep(1)
        with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
            task = crud_task.get_task_by_id(db_session, task_id)
            if task.state == "running":
                task.state = "failed"
                task.exception = "Worker finished before signalling success"
                db_session.commit()
                self.ui_subscription_manager.notify_task_update(task)
                logger.info("Task %s marked as failed", task_id)
        logger.info("Task %s finished", task_id)

    def subscribe_ui(self, ui_subscription_manager: "TaskUISubscriptionManager"):
        self._ui_subscription_manager = ui_subscription_manager