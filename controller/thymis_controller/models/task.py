from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, JsonValue

type TaskState = Literal["pending", "running", "completed", "failed"]

# sent from controller to frontend


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
    start_time: float
    end_time: Optional[float]
    exception: Optional[str]
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


class TaskShort(BaseModel):
    id: str  # uuid
    type: str
    display_name: str
    state: TaskState
    start_time: float
    end_time: Optional[float]
    exception: Optional[str]
    data: dict = {}  # freeform data


# sent from frontend to controller

# none yet

# sent from controller to task runner
# def create_deploy_project_task(self, devices: List[models.Hostkey]):
#         return task.global_task_controller.add_task(
#             task.DeployProjectTask(self, devices, global_settings.SSH_KEY_PATH)
#         )

#     def create_update_task(self):
#         return task.global_task_controller.add_task(task.UpdateTask(self.path, self))

#     def create_build_device_image_task(
#         self, device_identifier: str, db_session: Session
#     ):
#         self.commit(f"Build image for {device_identifier}")
#         device_state = next(
#             device
#             for device in self.read_state().devices
#             if device.identifier == device_identifier
#         )
#         return task.global_task_controller.add_task(
#             task.BuildDeviceImageTask(
#                 self.path,
#                 device_identifier,
#                 db_session,
#                 device_state.model_dump(),
#                 self.repo.head.object.hexsha,
#             )
#         )


#     def create_restart_device_task(self, device: models.Device, target_host: str):
#         return task.global_task_controller.add_task(
#             task.RestartDeviceTask(
#                 device, global_settings.SSH_KEY_PATH, self.known_hosts_path, target_host
#             )
#         )
class TaskSubmission(BaseModel):
    id: str  # uuid
    data: TaskSubmissionData


type TaskSubmissionData = Union[
    DeployProjectTaskSubmission,
    ProjectFlakeUpdateTaskSubmission,
    BuildDeviceImageTaskSubmission,
    SSHCommandTaskSubmission,
]


class DeployProjectTaskSubmission(BaseModel):
    devices: list[models.Hostkey]
    ssh_key_path: str


class ProjectFlakeUpdateTaskSubmission(BaseModel):
    pass


class BuildDeviceImageTaskSubmission(BaseModel):
    project_path: str
    device_identifier: str
    device_state: dict
    commit: str


class SSHCommandTaskSubmission(BaseModel):
    target_host: str
    command: str
    ssh_key_path: str
    ssh_known_hosts_path: str


# sent from task runner to controller

# none yet


__all__ = [
    "TaskState",
    "Task",
    "PlainTask",
    "CommandTask",
    "CompositeTask",
    "NixProcessStatus",
    "NixCommandTask",
]
