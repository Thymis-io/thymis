import asyncio
import base64
import concurrent.futures
import logging
import os
import sys
import threading
import traceback
import uuid
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime, timezone
from multiprocessing.connection import Connection, Pipe
from typing import TYPE_CHECKING, assert_never

import sqlalchemy.orm
import thymis_agent.agent as agent
import thymis_controller.crud as crud
import thymis_controller.crud.task as crud_task
import thymis_controller.models.task as models_task
from pyrage import ssh
from thymis_controller.notifier import Notifier
from thymis_controller.task.worker import worker_run_task

if TYPE_CHECKING:
    from thymis_controller.task.controller import TaskController

logger = logging.getLogger(__name__)


class TaskWorkerPoolManager:
    def __init__(self, controller: "TaskController"):
        self.pool = ProcessPoolExecutor()
        self.futures = {}
        self.future_to_id = {}
        self.listen_threads = {}
        self.controller = controller
        self._db_engine = None
        self.on_new_task = Notifier()
        self.on_task_update = Notifier()
        self.on_task_output = Notifier()

    @property
    def db_engine(self):
        if self._db_engine is None:
            raise ValueError("TaskWorkerPoolManager not started")
        return self._db_engine

    def submit(self, task_submission: models_task.TaskSubmission):
        executor_side, worker_side = Pipe()
        try:
            future = self.pool.submit(worker_run_task, task_submission, worker_side)
        except concurrent.futures.process.BrokenProcessPool:
            logger.error("Failed to submit task, process pool is closed")
            import signal

            os.kill(os.getpid(), signal.SIGINT)
            sys.exit(1)
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
            self.on_task_update.notify(task)
        try:
            self.send_message_to_task(
                task_id,
                models_task.ControllerToRunnerTaskUpdate(
                    inner=models_task.CancelTask(id=task_id)
                ),
            )
        except OSError as e:
            logger.error("Failed to send message to task %s: %s", task_id, e)

    def send_message_to_task(
        self, task_id: uuid.UUID, message: models_task.ControllerToRunnerTaskUpdate
    ):
        if task_id in self.futures:
            self.futures[task_id][1].send(message)

    def listen_child_messages(self, conn: Connection, task_id: uuid.UUID):
        message = None
        try:
            with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                task = crud_task.get_task_by_id(db_session, task_id)
                self.on_new_task.notify(task)

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
                try:
                    if not isinstance(
                        message, models_task.RunnerToControllerTaskUpdate
                    ):
                        logger.error(
                            "Received invalid message from worker: %s", message
                        )
                        continue
                    with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                        task = crud_task.get_task_by_id(db_session, message.id)
                        if task is None:
                            logger.error(
                                "Received message for unknown task: %s", message
                            )
                            continue
                        # logger.info("Received message from worker: %s", message)
                        match message.update:
                            case models_task.TaskPickedUpdate():
                                task.state = "running"
                                db_session.commit()
                            case models_task.TaskRejectedUpdate(reason=reason):
                                task.state = "failed"
                                task.add_exception(f"Task rejected: {reason}")
                                task.end_time = datetime.now(timezone.utc)
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
                                self.on_task_output.notify(task)
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
                                self.on_task_output.notify(task)
                            case models_task.TaskCompletedUpdate():
                                # task.state = "completed"
                                if not task.children:
                                    task.state = "completed"
                                    task.end_time = datetime.now(timezone.utc)
                                db_session.commit()
                                conn.close()
                                break
                            case models_task.TaskFailedUpdate(reason=reason):
                                task.state = "failed"
                                task.add_exception(reason)
                                task.end_time = datetime.now(timezone.utc)
                                logger.error("Task %s failed: %s", task_id, reason)
                                db_session.commit()
                                conn.close()
                                break
                            case models_task.CommandRunUpdate():
                                task.process_program = message.update.args[0]
                                task.process_args = message.update.args[1:]
                                task.process_env = message.update.env
                                db_session.commit()
                            case models_task.ImageBuiltUpdate():
                                crud.agent_token.create(
                                    db_session,
                                    original_disk_config_commit=message.update.configuration_commit,
                                    original_disk_config_id=message.update.configuration_id,
                                    token=message.update.token,
                                )

                                if message.update.image_format == "nixos-vm":
                                    # start a new task to start the VM
                                    if task.task_submission_data is None:
                                        raise ValueError("Task submission data is None")
                                    if "project_path" not in task.task_submission_data:
                                        raise ValueError(
                                            "project_path not in task submission data"
                                        )

                                    new_task_submission = models_task.RunNixOSVMTaskSubmission(
                                        configuration_id=message.update.configuration_id,
                                        parent_task_id=task_id,
                                        project_path=task.task_submission_data[
                                            "project_path"
                                        ],
                                    )
                                    new_task = self.controller.submit(
                                        new_task_submission,
                                        task.user_session_id,
                                        db_session,
                                    )
                                    db_session.commit()
                                else:
                                    self.controller.notification_manager.broadcast_image_built_notification(
                                        task.user_session_id,
                                        message.update.configuration_id,
                                        message.update.image_format,
                                    )
                            case (
                                models_task.AgentShouldSwitchToNewConfigurationUpdate()
                            ):
                                deployment_info = crud.deployment_info.get_by_id(
                                    db_session, message.update.deployment_info_id
                                )
                                relay_con_id = self.controller.network_relay.public_key_to_connection_id[
                                    deployment_info.ssh_public_key
                                ]
                                relay_con = self.controller.network_relay.registered_agent_connections[
                                    relay_con_id
                                ]
                                logger.info(
                                    "Switching agent to new configuration: %s",
                                    message.update.path_to_configuration,
                                )
                                asyncio.run_coroutine_threadsafe(
                                    relay_con.send_text(
                                        agent.RelayToAgentMessage(
                                            inner=agent.RtESwitchToNewConfigMessage(
                                                new_path_to_config=message.update.path_to_configuration,
                                                config_commit=message.update.config_commit,
                                                task_id=task_id,
                                            )
                                        ).model_dump_json()
                                    ),
                                    self.controller.network_relay.loop,
                                )
                            case models_task.WorkerRequestsSecretsUpdate():
                                # message.update.secret_ids
                                with sqlalchemy.orm.Session(
                                    bind=self.db_engine
                                ) as db_session:
                                    secrets = (
                                        self.controller.project.get_processed_secrets(
                                            db_session,
                                            message.update.secret_ids,
                                            message.update.target_recipient_token,
                                        )
                                    )
                                conn.send(
                                    models_task.ControllerToRunnerTaskUpdate(
                                        inner=models_task.SecretsResult(
                                            secrets=secrets,
                                        )
                                    )
                                )
                            case models_task.AgentShouldReceiveNewSecretsUpdate():
                                # message.update.secret_ids
                                with sqlalchemy.orm.Session(
                                    bind=self.db_engine
                                ) as db_session:
                                    secrets = self.controller.project.get_processed_secrets(
                                        db_session,
                                        [s.secret_id for s in message.update.secrets],
                                        ssh.Recipient.from_str(
                                            message.update.target_recipient_ssh_pubkey
                                        ),
                                    )
                                # send to agent
                                relay_con_id = self.controller.network_relay.public_key_to_connection_id[
                                    message.update.target_recipient_ssh_pubkey
                                ]
                                relay_con = self.controller.network_relay.registered_agent_connections[
                                    relay_con_id
                                ]
                                asyncio.run_coroutine_threadsafe(
                                    relay_con.send_text(
                                        agent.RelayToAgentMessage(
                                            inner=agent.RtESendSecretsMessage(
                                                secrets={
                                                    k: base64.b64encode(v).decode(
                                                        "utf-8"
                                                    )
                                                    for k, v in secrets.items()
                                                },
                                                secret_infos=message.update.secrets,
                                            )
                                        ).model_dump_json()
                                    ),
                                    self.controller.network_relay.loop,
                                )

                                conn.send(
                                    models_task.ControllerToRunnerTaskUpdate(
                                        inner=models_task.AgentGotNewSecretsResult(
                                            success=True
                                        )
                                    )
                                )

                            case _:
                                assert_never(message.update)

                        self.on_task_update.notify(task)
                except Exception as e:
                    traceback.print_exc()
                    logger.error("Error processing message from worker: %s", e)
        except EOFError:
            logger.info("Worker connection closed")
        except OSError as e:
            logger.info("Worker connection closed: %s", e)
        if message:
            with sqlalchemy.orm.Session(bind=self.db_engine) as db_session:
                task = crud_task.get_task_by_id(db_session, message.id)
                self.on_task_update.notify(task)
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
                self.on_task_update.notify(task)

            if "pending" in child_states or "running" in child_states:
                return

            if set(["completed"]) == child_states:
                task.state = "completed"

            if not task.end_time:
                task.end_time = datetime.now(timezone.utc)

            db_session.commit()
            self.on_task_update.notify(task)

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
                task.end_time = datetime.now(timezone.utc)
                task.add_exception("Worker finished before signalling success")
                db_session.commit()
                self.on_task_update.notify(task)
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
                    self.on_task_update.notify(parent_task)

            logger.info("Task %s finished with state %s", task_id, task.state)
            if "RUNNING_IN_PLAYWRIGHT" in os.environ and task.state == "failed":
                logger.error("Task submission data for task %s:", task_id)
                logger.error(task.task_submission_data)
                logger.error("Task error for task %s:", task_id)
                logger.error(task.exception)
                logger.error("STDOUT for task %s:", task_id)
                if task.process_stdout:
                    logger.error(task.process_stdout.decode("utf-8"))
                else:
                    logger.error("No stdout")
                logger.error("STDERR for task %s:", task_id)
                if task.process_stderr:
                    logger.error(task.process_stderr.decode("utf-8"))
                else:
                    logger.error("No stderr")
                logger.error("Nix status for task %s:", task_id)
                if task.nix_status:
                    logger.error(task.nix_status)
                else:
                    logger.error("No nix status")
                logger.error("Nix errors for task %s:", task_id)
                if task.nix_errors:
                    logger.error(task.nix_errors)
                else:
                    logger.error("No nix errors")
                logger.error("Nix error logs for task %s:", task_id)
                if task.nix_error_logs:
                    logger.error(task.nix_error_logs)
                else:
                    logger.error("No nix error logs")
                logger.error("Nix warning logs for task %s:", task_id)
                if task.nix_warning_logs:
                    logger.error(task.nix_warning_logs)
                else:
                    logger.error("No nix warning logs")
                logger.error("Nix notice logs for task %s:", task_id)
                if task.nix_notice_logs:
                    logger.error(task.nix_notice_logs)
                else:
                    logger.error("No nix notice logs")
                logger.error("Nix info logs for task %s:", task_id)
                if task.nix_info_logs:
                    logger.error(task.nix_info_logs)
                else:
                    logger.error("No nix info logs")
