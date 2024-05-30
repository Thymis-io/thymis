import asyncio
import json
import os
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from thymis_controller import models, project


class Task:
    display_name: str
    state: models.TaskState
    exception: Optional[Exception]

    def __init__(self):
        self.state = "pending"
        self.exception = None

        all_tasks.append(self)

    async def __call__(self, *args, **kwargs):
        self.state = "running"
        await send_all_tasks()
        try:
            await self.run(*args, **kwargs)
            self.state = "completed"
            await send_all_tasks()
        except Exception as e:
            self.state = "failed"
            self.exception = e
            await send_all_tasks()
            raise e

    async def run(self, *args, **kwargs):
        raise NotImplementedError()

    def get_model(self) -> models.Task:
        return models.Task(
            display_name=self.display_name,
            state=self.state,
            exception=self.exception,
        )


all_tasks: list[Task] = []


class ConnectionManager:
    active_connections: list[WebSocket]

    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            while True:
                await websocket.receive_bytes()
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_broadcast(self, data: str):
        for connection in self.active_connections:
            await connection.send_text(data)


connection_manager = ConnectionManager()


async def send_all_tasks():
    await connection_manager.send_broadcast(
        json.dumps(jsonable_encoder([task.get_model() for task in all_tasks]))
    )


async def stream_reader(
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
        await send_all_tasks()


class CompositeTask(Task):
    tasks: list[Task]

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        self.display_name = f"Running {len(tasks)} tasks"

    async def run(self):
        await asyncio.gather(*[task() for task in self.tasks])

    def get_model(self) -> models.CompositeTask:
        return models.CompositeTask(
            display_name=self.display_name,
            state=self.state,
            exception=self.exception,
            tasks=[task.get_model() for task in self.tasks],
        )


class CommandTask(Task):
    program: str
    args: list[str]
    env: Optional[dict[str, str]]
    stdout: bytearray
    stderr: bytearray

    def __init__(self, program, args, env=None):
        super().__init__()

        self.program = program
        self.args = args
        self.env = env

        self.display_name = f"Running `{program} {' '.join(str(arg) for arg in args)}`"

        self.stdout = bytearray()
        self.stderr = bytearray()

    async def run(self):
        proc = await asyncio.create_subprocess_exec(
            self.program,
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )

        asyncio.create_task(stream_reader(proc.stdout, self.stdout))
        asyncio.create_task(stream_reader(proc.stderr, self.stderr))

        r = await proc.wait()
        if r != 0:
            raise Exception(
                f"Command {self.program} {' '.join(self.args)} failed with exit code {r}"
            )
        return r

    def get_model(self) -> models.CommandTask:
        return models.CommandTask(
            display_name=self.display_name,
            state=self.state,
            exception=str(self.exception),
            stdout=self.stdout.decode(),
            stderr=self.stderr.decode(),
        )


class BuildTask(CommandTask):
    def __init__(self, repo_dir):
        super().__init__(
            "nix", ["build", f"{repo_dir}#thymis", "--out-link", "/tmp/thymis"]
        )

        self.display_name = f"Building project"


class DeployProjectTask(CompositeTask):
    def __init__(self, project: "project.Project"):
        super().__init__(
            [
                DeployDeviceTask(project.path, device)
                for device in project.read_state().devices
            ]
        )

        self.display_name = "Deploying project"


class DeployDeviceTask(CommandTask):
    def __init__(self, repo_dir, device: models.Device):
        super().__init__(
            "nixos-rebuild",
            [
                "switch",
                "--flake",
                f"{repo_dir}#{device.identifier}",
                "--target-host",
                f"root@{device.targetHost}",
            ],
            env={
                "NIX_SSHOPTS": "-o StrictHostKeyChecking=accept-new",
                "PATH": os.getenv("PATH"),
            },
        )

        self.display_name = f"Deploying to {device.targetHost}"


class UpdateTask(CommandTask):
    def __init__(self, repo_dir):
        super().__init__("nix", ["flake", "update", repo_dir])


class BuildDeviceImageTask(CommandTask):
    def __init__(self, repo_dir, identifier):
        super().__init__(
            "nix",
            [
                "build",
                f'{repo_dir}#nixosConfigurations."{identifier}".config.formats.sd-card-image',
                "--out-link",
                f"/tmp/thymis-devices.{identifier}",
            ],
        )

        self.display_name = f"Building image for {identifier}"
