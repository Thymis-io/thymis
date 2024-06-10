from typing import Literal, Optional

from pydantic import BaseModel

TaskState = Literal["pending", "running", "completed", "failed"]


class Task(BaseModel):
    type: Literal["task"] = "task"
    display_name: str
    state: TaskState
    exception: Optional[str]
    start_time: float
    data: dict = {}


class CommandTask(Task):
    type: Literal["commandtask"] = "commandtask"
    stdout: str
    stderr: str


class CompositeTask(Task):
    type: Literal["compositetask"] = "compositetask"
    tasks: list[Task]


__all__ = ["TaskState", "Task", "CommandTask", "CompositeTask"]
