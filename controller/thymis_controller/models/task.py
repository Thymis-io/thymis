from typing import Literal, Optional

from pydantic import BaseModel

TaskState = Literal["pending", "running", "completed", "failed"]


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


class CompositeTask(Task):
    type: Literal["compositetask"] = "compositetask"
    tasks: list[Task]


__all__ = ["TaskState", "Task", "CommandTask", "CompositeTask"]
