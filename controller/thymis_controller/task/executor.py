import base64
import concurrent.futures
import logging
import threading
import uuid
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime
from multiprocessing.connection import Connection, Pipe
from typing import assert_never

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
        executor_side, worker_side = Pipe()
        future = self.pool.submit(worker_run_task, task_submission, worker_side)
        future.add_done_callback(self.finish_task)
        self.futures[task_submission.id] = (future, executor_side)
        self.future_to_id[future] = task_submission.id
        thread = threading.Thread(
            target=self.listen_child_messages,
            args=(executor_side, task_submission.id),
        )
        thread.start()
        self.listen_threads[task_submission.id] = thread

    async def start(self, db_engine: sqlalchemy.Engine):
        self._db_engine = db_engine

        with (sqlalchemy.orm.Session(bind=self.db_engine) as db_session,):
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
        logger.info("Stopping TaskWorkerPoolManager")
        # join all pending futures
        concurrent.futures.wait([future for future, _ in self.futures.values()])
        logger.info("All worker futures finished")
        # close all worker connections
        for _, child_out in self.futures.values():
            child_out.close()
        logger.info("All worker connections closed")
        for thread in self.listen_threads.values():
            thread.join()
        logger.info("All listen threads joined")
        self.pool.shutdown(wait=True)
        logger.info("TaskWorkerPoolManager stopped")

    def cancel_task(self, task_id: uuid.UUID):
        with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
            task = crud_task.get_task_by_id(db_session, task_id)
            task.add_exception("Task was cancelled")
            db_session.commit()
            self.ui_subscription_manager.notify_task_update(task)
        if task_id in self.futures:
            self.futures[task_id][1].send(models_task.CancelTask(id=task_id))

    def cancel_all_tasks(self):
        future_tasks = list(self.futures.keys())
        for task_id in future_tasks:
            if (
                task_id in self.futures
                and self.futures[task_id][0].running()
                and not self.futures[task_id][1].closed
            ):
                self.cancel_task(task_id)

    def listen_child_messages(self, conn: Connection, task_id: uuid.UUID):
        message = None
        try:
            with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                task = crud_task.get_task_by_id(db_session, task_id)
                self.ui_subscription_manager.notify_new_task(task)

            while True:
                message_avail = conn.poll(0.5)
                if not message_avail:
                    if not task_id in self.futures:
                        logger.info("Task %s no longer in futures", task_id)
                        break
                    if not self.futures[task_id][0].running():
                        logger.error(
                            "Task %s future is not running, no message available, but future is not popped",
                            task_id,
                        )
                    continue
                message = conn.recv()
                if not isinstance(message, models_task.RunnerToControllerTaskUpdate):
                    logger.error("Received invalid message from worker: %s", message)
                    continue
                with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                    task = crud_task.get_task_by_id(db_session, message.id)
                    if task is None:
                        logger.error("Received message for unknown task: %s", message)
                        continue
                    # logger.info("Received message from worker: %s", message)
                    match message.update:
                        case models_task.TaskPickedUpdate():
                            task.state = "running"
                            db_session.commit()
                        case models_task.TaskRejectedUpdate(reason=reason):
                            task.state = "failed"
                            task.add_exception(f"Task rejected: {reason}")
                            task.end_time = datetime.now()
                            db_session.commit()
                        case models_task.TaskStdOutErrUpdate(
                            stdoutb64=stdoutb64, stderrb64=stderrb64
                        ):
                            # initialize stdout and stderr if not already set
                            if task.process_stdout is None:
                                task.process_stdout = b""
                            if task.process_stderr is None:
                                task.process_stderr = b""
                            # append new data to stdout and stderr
                            task.process_stdout += base64.b64decode(stdoutb64)
                            task.process_stderr += base64.b64decode(stderrb64)
                            db_session.commit()
                        case models_task.TaskNixStatusUpdate(status=status):
                            task.nix_status = status.model_dump(
                                include=("done", "expected", "running", "failed")
                            )
                            task.nix_errors = status.model_dump(include=("errors"))[
                                "errors"
                            ]
                            task.nix_error_logs = status.logs_by_level.get(0)
                            task.nix_warning_logs = status.logs_by_level.get(1)
                            task.nix_notice_logs = status.logs_by_level.get(2)
                            task.nix_info_logs = status.logs_by_level.get(3)
                            db_session.commit()
                        case models_task.TaskCompletedUpdate():
                            task.state = "completed"
                            task.end_time = datetime.now()
                            db_session.commit()
                            conn.close()
                            break
                        case models_task.TaskFailedUpdate(reason=reason):
                            task.state = "failed"
                            task.add_exception(reason)
                            task.end_time = datetime.now()
                            db_session.commit()
                            conn.close()
                            break
                        case models_task.CommandRunUpdate():
                            task.process_program = message.update.args[0]
                            task.process_args = message.update.args[1:]
                            task.process_env = message.update.env
                            db_session.commit()
                        case _:
                            assert_never(message.update)

                    # notify UI
                    self.ui_subscription_manager.notify_task_update(task)
        except EOFError:
            logger.info("Worker connection closed")
        except OSError as e:
            logger.info("Worker connection closed: %s", e)
        if message:
            with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                task = crud_task.get_task_by_id(db_session, message.id)
                self.ui_subscription_manager.notify_task_update(task)
        conn.close()

    def update_composite_task(self, task_id: uuid.UUID):
        with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
            task = crud_task.get_task_by_id(db_session, task_id)

            if not task.children:
                return

            child_states = crud_task.child_task_states(
                db_session, [uuid.UUID(child) for child in task.children]
            )

            if "failed" in child_states and task.state != "failed":
                task.state = "failed"
                db_session.commit()
                self.ui_subscription_manager.notify_task_update(task)

            if "pending" in child_states or "running" in child_states:
                return

            if set(["completed"]) == child_states:
                task.state = "completed"

            if not task.end_time:
                task.end_time = datetime.now()

            db_session.commit()
            self.ui_subscription_manager.notify_task_update(task)

    def finish_task(self, future: Future):
        task_id = self.future_to_id[future]
        future, child_out = self.futures.pop(task_id)
        # join listen thread
        logger.info("Task %s worker finished, joining listen thread", task_id)
        self.listen_threads[task_id].join()
        logger.info("Task %s worker finished execution", task_id)
        # if task is still running in the database, mark it as failed due to worker finishing before signalling success
        with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
            task = crud_task.get_task_by_id(db_session, task_id)

            if task.children:
                self.update_composite_task(task_id)
            elif task.state == "running" or task.state == "pending":
                task.state = "failed"
                task.add_exception("Worker finished before signalling success")
                db_session.commit()
                self.ui_subscription_manager.notify_task_update(task)
                logger.info("Task %s marked as failed", task_id)

            if task.parent_task_id:
                self.update_composite_task(task.parent_task_id)

                if task.state == "failed":
                    parent_task = crud_task.get_task_by_id(
                        db_session, task.parent_task_id
                    )

                    parent_task.add_exception(f"Child Task {task_id} failed")

                    # TODO: Remove direct writing to stderr and show child progress in UI
                    if parent_task.process_stderr is None:
                        parent_task.process_stderr = b""

                    parent_task.process_stderr += (
                        f"Child Task {task_id} failed\n".encode("utf-8")
                    )

                    db_session.commit()
                    self.ui_subscription_manager.notify_task_update(parent_task)

        logger.info("Task %s finished", task_id)

    def subscribe_ui(self, ui_subscription_manager: "TaskUISubscriptionManager"):
        self._ui_subscription_manager = ui_subscription_manager
