from typing import Any, Literal, Optional

from pydantic import BaseModel, JsonValue

type TaskState = Literal["pending", "running", "completed", "failed"]


class NixProcessStatus(BaseModel):
    done: int
    expected: int
    running: int
    failed: int
    errors: list[Any] = []
    logs_by_level: dict[int, list[str]] = {}


class Task(BaseModel):
    id: str  # uuid
    type: str
    display_name: str
    state: TaskState
    exception: Optional[str]
    start_time: float
    end_time: Optional[float]
    data: dict = {}  # freeform data


class PlainTask(Task):
    type: Literal["task"] = "task"


class CommandTask(Task):
    type: Literal["commandtask"] = "commandtask"
    stdout: str
    stderr: str


class NixCommandTask(CommandTask):
    type: Literal["nixcommandtask"] = "nixcommandtask"
    status: NixProcessStatus


class CompositeTask(Task):
    type: Literal["compositetask"] = "compositetask"
    tasks: list[Task]


__all__ = [
    "TaskState",
    "Task",
    "CommandTask",
    "CompositeTask",
    "NixProcessStatus",
    "NixCommandTask",
]
