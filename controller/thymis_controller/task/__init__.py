import asyncio
import collections
import copy
import json
import logging
import os
import time
import uuid
from typing import List, Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from thymis_controller import crud, models, project
from thymis_controller.config import global_settings
from thymis_controller.nix import NIX_CMD, get_build_output

logger = logging.getLogger(__name__)


class TaskController:
    all_tasks_list: list["Task"]
    all_tasks_dict: dict[uuid.UUID, "Task"]
    # task_queue: list["Task"]
    task_queue: collections.deque["Task"]
    running_tasks: list["Task"]
    barriers: dict[uuid.UUID, asyncio.Barrier]

    active_listeners: list[WebSocket]

    task_limit: int

    def __init__(self):
        self.all_tasks_list = []
        self.all_tasks_dict = {}
        self.task_limit = 5
        self.task_queue = (
            collections.deque()
        )  # left is processed last, right is processed first
        self.running_tasks = []
        self.active_listeners = []
        self.barriers = {}

    def count_command_tasks_running(self):
        return len(
            [task for task in self.running_tasks if isinstance(task, CommandTask)]
        )

    async def add_task(
        self, task: "Task", go_to_front=False, barrier: asyncio.Barrier = None
    ):
        task.controller = self

        self.all_tasks_list.append(task)
        self.all_tasks_dict[task.id] = task

        if barrier is not None:
            self.barriers[task.id] = barrier

        if go_to_front:
            self.task_queue.append(task)
        else:
            self.task_queue.appendleft(task)

        await self.try_run_front_of_queue()
        await self.send_all_tasks()

    async def try_run_front_of_queue(self):
        if self.count_command_tasks_running() >= self.task_limit:
            return
        if len(self.task_queue) == 0:
            return

        task = self.task_queue.pop()
        self.running_tasks.append(task)
        task.state = "running"
        asyncio.create_task(task.run())
        await self.send_all_tasks()

    async def cleanup_task(self, task: "Task"):
        # self.running_tasks.remove(task)
        # task may have been cancelled from pending state
        if task.state == "running":
            # check if task is in the running list
            if not task in self.running_tasks:
                raise ValueError("Task has state running, but is not in running list")
            raise ValueError("Task is still running, but wants to be cleaned up")
        elif task.state == "pending":
            if not task in self.task_queue:
                raise ValueError("Task has state pending, but is not in queue")
            raise ValueError("Task is still pending, but wants to be cleaned up")
        elif task.state == "completed":
            if task in self.task_queue:
                raise ValueError("Task is completed, but still in queue")
            if task in self.running_tasks:
                self.running_tasks.remove(task)
        elif task.state == "failed":
            # self.running_tasks.remove(task)
            if task in self.running_tasks:
                self.running_tasks.remove(task)
            if task in self.task_queue:
                self.task_queue.remove(task)
        else:
            raise ValueError("Task has invalid state")
        await self.send_all_tasks()
        await self.try_run_front_of_queue()

    async def send_all_tasks(self):
        await self.send_broadcast(json.dumps(jsonable_encoder(self.get_tasks())))

    async def send_broadcast(self, data: str):
        for connection in self.active_listeners:
            await connection.send_text(data)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_listeners.append(websocket)
        await self.send_all_tasks()
        try:
            while True:
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_listeners.remove(websocket)

    async def cancel_task(self, task_id: uuid.UUID):
        task = self.all_tasks_dict.get(task_id)
        if task is None:
            raise ValueError("Task not found")
        if task.state == "pending":
            self.task_queue.remove(task)
        elif task.state == "running":
            self.running_tasks.remove(task)
        await task.cancel()
        await self.send_all_tasks()

    async def retry_task(self, task_id: uuid.UUID):
        task = self.all_tasks_dict.get(task_id)
        if task is None:
            raise ValueError("Task not found")
        if task.state not in ["completed", "failed"]:
            raise ValueError("Task is not in a retryable state")
        # create a new task with the same parameters
        new_task = task.copy_for_retry()
        await self.add_task(new_task)

    async def run_immediately(self, task_id: uuid.UUID):
        task = self.all_tasks_dict.get(task_id)
        if task is None:
            raise ValueError("Task not found")
        if task.state == "pending":
            self.task_queue.remove(task)
            self.running_tasks.append(task)
            task.state = "running"
            asyncio.create_task(task.run())
        await self.send_all_tasks()

    def get_task(self, task_id: uuid.UUID):
        self.check_consistency()
        # print queue
        logger.info(f"Task queue: {self.task_queue}")
        task = self.all_tasks_dict.get(task_id)
        if task is None:
            raise ValueError("Task not found")
        return task.get_model()

    def get_tasks(self):
        self.check_consistency()
        return [task.get_model() for task in self.all_tasks_list]

    def check_consistency(self):
        return
        for task in self.all_tasks_list:
            assert task in self.all_tasks_dict.values()
        for task in self.task_queue:
            assert task in self.all_tasks_list
            assert task.state == "pending"
        for task in self.running_tasks:
            assert task in self.all_tasks_list
            assert task.state == "running"
        for task_id in self.barriers:
            assert task_id in self.all_tasks_dict
        for task in self.all_tasks_dict.values():
            assert task in self.all_tasks_list
        for task in self.task_queue:
            assert task not in self.running_tasks
        for task in self.running_tasks:
            assert task not in self.task_queue


global_task_controller = TaskController()


class Task:
    id: uuid.UUID
    start_time: float
    end_time: Optional[float]
    display_name: str
    state: models.TaskState
    exception: Optional[Exception]
    controller: TaskController

    cancelled: bool

    def __init__(self, display_name: str):
        self.id = uuid.uuid4()
        self.display_name = display_name
        self.state = "pending"
        self.exception = None
        self.start_time = time.time()
        self.end_time = None
        self.controller = None
        self.cancelled = False

    def get_model(self):
        return models.PlainTask(
            id=self.id,
            start_time=self.start_time,
            end_time=self.end_time,
            display_name=self.display_name,
            state=self.state,
            exception=str(self.exception),
        )

    async def run(self):
        await self.controller.send_all_tasks()
        try:
            await self._run()
            self.end_time = time.time()
            if not self.cancelled:
                self.state = "completed"
            await self.controller.cleanup_task(self)
            if self.controller.barriers.get(self.id) is not None:
                await self.controller.barriers[self.id].wait()
        except Exception as e:
            self.end_time = time.time()
            if not self.cancelled:
                self.state = "failed"
                self.exception = e
            await self.controller.cleanup_task(self)
            if self.controller.barriers.get(self.id) is not None:
                await self.controller.barriers[self.id].wait()
            if not self.cancelled:
                raise e

    async def _run(self):
        raise NotImplementedError()

    async def cancel(self):
        self.cancelled = True
        # only works if the current task is pending
        if self.state != "pending":
            raise ValueError("Task is not pending")
        self.state = "failed"
        self.exception = Exception("Task was cancelled")
        self.end_time = time.time()
        await self.controller.cleanup_task(self)

    def copy_for_retry(self):
        new_task = copy.copy(self)
        new_task.id = uuid.uuid4()
        new_task.start_time = time.time()
        new_task.end_time = None
        new_task.state = "pending"
        new_task.exception = None
        new_task.controller = None
        new_task.cancelled = False
        return new_task


class CommandTask(Task):
    program: str
    args: list[str]
    env: Optional[dict[str, str]]
    stdout: bytearray
    stderr: bytearray

    process: asyncio.subprocess.Process

    def __init__(self, program, args, env=None):
        super().__init__(f"Running `{program} {' '.join(str(arg) for arg in args)}`")

        self.program = program
        self.args = args
        self.env = env

        self.stdout = bytearray()
        self.stderr = bytearray()

        self.cancelled = False
        self.process = None

    async def _run(self):
        proc = await asyncio.create_subprocess_exec(
            self.program,
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )
        self.process = proc

        read_stdout_task = asyncio.create_task(
            self.stream_reader(proc.stdout, self.stdout)
        )
        read_stderr_task = asyncio.create_task(
            self.stream_reader(proc.stderr, self.stderr)
        )

        r = await proc.wait()
        if r != 0:
            raise RuntimeError(
                f"Command {self.program} {' '.join(self.args)} failed with exit code {r}"
            )

        await asyncio.gather(read_stdout_task, read_stderr_task)

        return r

    async def stream_reader(
        self,
        stream: asyncio.StreamReader | None,
        out: bytearray,
    ):
        while True:
            line = await stream.readline()
            if not line:
                # readline doc:
                # On success, return chunk that ends with newline.
                # If only partial line can be read due to EOF,
                # return incomplete line without terminating newline.
                # When EOF was reached while no bytes read, empty bytes object is returned.
                #
                # So, if line is empty, we have reached EOF
                break
            out.extend(line)
            await self.controller.send_all_tasks()

    def get_model(self) -> models.CommandTask:
        return models.CommandTask(
            id=str(self.id),
            type="commandtask",
            display_name=self.display_name,
            start_time=self.start_time,
            end_time=self.end_time,
            state=self.state,
            exception=str(self.exception),
            stdout=self.stdout.decode(),
            stderr=self.stderr.decode(),
            data={"program": self.program, "args": self.args, "env": self.env},
        )

    async def cancel(self):
        # CommandTasks may be cancelled while pending and running
        self.cancelled = True
        if self.state == "pending":
            self.state = "failed"
            self.exception = Exception("Task was cancelled")
            self.end_time = time.time()
            await self.controller.cleanup_task(self)
        elif self.state == "running":
            # we have to kill the process
            self.process.kill()
            self.state = "failed"
            self.exception = Exception("Task was killed")
            self.end_time = time.time()
            await self.controller.cleanup_task(self)
        else:
            raise ValueError(
                f"Task {self.id} is not pending or running but {self.state}"
            )

    def copy_for_retry(self):
        new_task = copy.copy(self)
        new_task.id = uuid.uuid4()
        new_task.start_time = time.time()
        new_task.end_time = None
        new_task.state = "pending"
        new_task.exception = None
        new_task.controller = None
        new_task.cancelled = False
        new_task.stdout = bytearray()
        new_task.stderr = bytearray()
        new_task.process = None
        return new_task


class CompositeTask(Task):
    tasks: list[Task]

    def __init__(self, tasks):
        super().__init__(f"Running {len(tasks)} tasks")

        self.tasks = tasks

    async def _run(self):
        # queues subtasks at the front of the queue
        bar = asyncio.Barrier(len(self.tasks) + 1)
        for task in self.tasks:
            await self.controller.add_task(task, go_to_front=True, barrier=bar)
        await bar.wait()
        # if any subtask failed, the composite task fails
        if any(task.state == "failed" for task in self.tasks):
            raise RuntimeError("One or more subtasks failed")

    def get_model(self) -> models.CompositeTask:
        return models.CompositeTask(
            id=str(self.id),
            type="compositetask",
            start_time=self.start_time,
            end_time=self.end_time,
            display_name=self.display_name,
            state=self.state,
            exception=str(self.exception),
            tasks=[task.get_model() for task in self.tasks],
        )

    async def cancel(self):
        self.cancelled = True
        # CompositeTasks may be cancelled while pending and running
        if self.state == "pending":
            self.state = "failed"
            self.exception = Exception("Task was cancelled")
            self.end_time = time.time()
            await self.controller.cleanup_task(self)
        elif self.state == "running":
            self.state = "failed"
            self.exception = Exception("Task was cancelled")
            self.end_time = time.time()
            # cancel all subtasks
            for task in self.tasks:
                if task.state == "running" or task.state == "pending":
                    await task.cancel()
            await self.controller.cleanup_task(self)
        else:
            raise ValueError("Task is not pending or running")

    def copy_for_retry(self):
        subtasks = []
        for task in self.tasks:
            subtasks.append(task.copy_for_retry())
        new_task = copy.copy(self)
        new_task.id = uuid.uuid4()
        new_task.start_time = time.time()
        new_task.end_time = None
        new_task.state = "pending"
        new_task.exception = None
        new_task.controller = None
        new_task.cancelled = False

        new_task.tasks = subtasks
        return new_task


class BuildTask(CommandTask):
    def __init__(self, repo_dir):
        super().__init__(
            "nix",
            [*NIX_CMD[1:], "build", f"{repo_dir}#thymis", "--out-link", "/tmp/thymis"],
        )

        self.display_name = "Building project"


class DeployProjectTask(CompositeTask):
    def __init__(
        self,
        project: "project.Project",
        devices: List[models.RegisteredDevice],
        ssh_key_path: str,
    ):
        deployable_devices = []
        for device in devices:
            state = next(
                state
                for state in project.read_state().devices
                if state.identifier == device.identifier
            )
            if state:
                deployable_devices.append((device.device_host, state))

        super().__init__(
            [
                DeployDeviceTask(
                    project.path,
                    state,
                    ssh_key_path,
                    project.known_hosts_path,
                    target_host,
                )
                for target_host, state in deployable_devices
            ]
        )

        self.display_name = "Deploying project"


class DeployDeviceTask(CommandTask):
    def __init__(
        self,
        repo_dir,
        device: models.Device,
        ssh_key_path: str,
        known_hosts_path,
        target_host,
    ):
        super().__init__(
            "nixos-rebuild",
            [
                *NIX_CMD[1:],
                "switch",
                "--flake",
                f"{repo_dir}#{device.identifier}",
                "--target-host",
                f"root@{target_host}",
            ],
            env={
                "NIX_SSHOPTS": f"-i {ssh_key_path} -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile={known_hosts_path}",
                "PATH": os.getenv("PATH"),
            },
        )

        self.display_name = f"Deploying to {target_host}"


class UpdateTask(CommandTask):
    def __init__(self, repo_dir):
        super().__init__("nix", [*NIX_CMD[1:], "flake", "update", repo_dir])


class BuildDeviceImageTask(CommandTask):
    image_path: str
    db_session: Session
    build_hash: str

    def __init__(self, repo_dir, identifier, db_session, device_state, commit_hash):
        super().__init__(
            "nix",
            [
                *NIX_CMD[1:],
                "build",
                f'{repo_dir}#nixosConfigurations."{identifier}".config.formats.sd-card-image',
                "--out-link",
                f"/tmp/thymis-devices.{identifier}",
            ],
        )

        self.display_name = f"Building image for {identifier}"
        self.identifier = identifier
        self.image_path = f"/tmp/thymis-devices.{identifier}"
        self.build_hash = None
        self.db_session = db_session
        self.device_state = device_state
        self.commit_hash = commit_hash

    async def _run(self):
        r = await super()._run()
        if r != 0:
            return

        build_output = get_build_output(global_settings.REPO_PATH, self.identifier)

        store_path = build_output["outputs"]["out"]  # TODO: or maybe drvPath?
        self.build_hash = store_path[len("/nix/store/") :].split("-")[0]

        crud.image.create(
            self.db_session,
            self.identifier,
            self.build_hash,
            self.device_state,
            self.commit_hash,
        )

        return r

    def get_model(self) -> models.CommandTask:
        return models.CommandTask(
            id=str(self.id),
            type="commandtask",
            display_name=self.display_name,
            start_time=self.start_time,
            end_time=self.end_time,
            state=self.state,
            exception=str(self.exception),
            stdout=self.stdout.decode(),
            stderr=self.stderr.decode(),
            data={
                "identifier": self.identifier,
                "program": self.program,
                "args": self.args,
            },
        )


class RestartDeviceTask(CommandTask):
    def __init__(
        self, device: models.Device, key_path: str, known_hosts_path, target_host
    ):
        super().__init__(
            "ssh",
            [
                "-o StrictHostKeyChecking=accept-new",
                f"-o UserKnownHostsFile={known_hosts_path}",
                "-o ConnectTimeout=30",
                f"-i{key_path}",
                f"root@{target_host}",
                "reboot",
            ],
        )

        self.display_name = f"Restarting {device.displayName}"
        self.identifier = device.identifier
