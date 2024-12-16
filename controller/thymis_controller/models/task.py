import datetime
import uuid
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, JsonValue

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
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID  # uuid
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    state: TaskState
    exception: Optional[str]
    task_type: str
    task_submission_data: "TaskSubmissionData"

    parent_task_id: Optional[uuid.UUID] = None
    children: Optional[list[uuid.UUID]] = None

    process_program: Optional[str]
    process_args: Optional[list[str]]
    process_env: Optional[dict[str, str]]
    process_stdout: Optional[str]
    process_stderr: Optional[str]

    nix_status: Optional[NixProcessStatus]
    nix_files_linked: Optional[int]
    nix_bytes_linked: Optional[int]
    nix_corrupted_paths: Optional[int]
    nix_untrusted_paths: Optional[int]
    nix_errors: Optional[JsonValue]
    nix_warnings: Optional[JsonValue]
    nix_notices: Optional[JsonValue]
    nix_infos: Optional[JsonValue]


class TaskShort(BaseModel):
    id: uuid.UUID  # uuid
    task_type: str
    state: TaskState
    start_time: datetime.datetime
    end_time: Optional[float]
    exception: Optional[str]
    task_submission_data: "TaskSubmissionData"


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
    id: uuid.UUID  # uuid
    data: "TaskSubmissionData" = Field(discriminator="type")

    @classmethod
    def from_orm(cls, task: Task) -> "TaskSubmission":
        return cls(id=task.id, data=task.task_submission_data)


type TaskSubmissionData = Union[
    "DeployDevicesTaskSubmission",
    "ProjectFlakeUpdateTaskSubmission",
    "BuildDeviceImageTaskSubmission",
    "SSHCommandTaskSubmission",
]


class DeployDeviceInformation(BaseModel):
    identifier: str
    host: str
    port: int
    username: str


class DeployDevicesTaskSubmission(BaseModel):
    type: Literal["deploy_devices_task"] = "deploy_devices_task"
    devices: list[DeployDeviceInformation]
    ssh_key_path: str
    known_hosts_path: str
    parent_task_id: Optional[uuid.UUID] = None


class DeployDeviceTaskSubmission(BaseModel):
    type: Literal["deploy_device_task"]
    device: DeployDeviceInformation
    ssh_key_path: str
    known_hosts_path: str


class ProjectFlakeUpdateTaskSubmission(BaseModel):
    type: Literal["project_flake_update_task"] = "project_flake_update_task"
    project_path: str


class BuildDeviceImageTaskSubmission(BaseModel):
    type: Literal["build_device_image_task"] = "build_device_image_task"
    project_path: str
    device_identifier: str
    device_state: dict
    commit: str


class SSHCommandTaskSubmission(BaseModel):
    type: Literal["ssh_command_task"] = "ssh_command_task"
    target_host: str
    command: str
    ssh_key_path: str
    ssh_known_hosts_path: str


# sent from task runner to controller


class RunnerToControllerTaskUpdate(BaseModel):
    id: uuid.UUID  # uuid of the task
    update: "TaskUpdate" = Field(discriminator="type")


TaskUpdate = Union[
    "TaskPickedUpdate",
    "TaskRejectedUpdate",
]


class TaskPickedUpdate(BaseModel):
    type: Literal["task_picked"] = "task_picked"


class TaskRejectedUpdate(BaseModel):
    type: Literal["task_rejected"] = "task_rejected"
    reason: str


__all__ = [
    "TaskState",
    "Task",
    "NixProcessStatus",
    "TaskShort",
    "TaskSubmission",
    "TaskSubmissionData",
    "DeployDeviceInformation",
    "DeployDevicesTaskSubmission",
    "ProjectFlakeUpdateTaskSubmission",
    "BuildDeviceImageTaskSubmission",
    "SSHCommandTaskSubmission",
    "RunnerToControllerTaskUpdate",
    "TaskPickedUpdate",
    "TaskRejectedUpdate",
    "TaskUpdate",
]
