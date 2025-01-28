import datetime
import uuid
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, JsonValue
from thymis_controller.nix.log_parse import ParsedNixProcess

type TaskState = Literal["pending", "running", "completed", "failed"]

# sent from controller to frontend


class NixProcessStatus(BaseModel):
    done: int
    expected: int
    running: int
    failed: int


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
    nix_errors: Optional[JsonValue]
    nix_files_linked: Optional[int]
    nix_bytes_linked: Optional[int]
    nix_corrupted_paths: Optional[int]
    nix_untrusted_paths: Optional[int]
    nix_error_logs: Optional[JsonValue]
    nix_warning_logs: Optional[JsonValue]
    nix_notice_logs: Optional[JsonValue]
    nix_info_logs: Optional[JsonValue]


class TaskShort(BaseModel):
    id: uuid.UUID  # uuid
    task_type: str
    state: TaskState
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    exception: Optional[str]
    task_submission_data: "TaskSubmissionData"
    nix_status: Optional[NixProcessStatus]

    @classmethod
    def from_orm_task(cls, task: Task) -> "TaskShort":
        return cls(
            id=task.id,
            task_type=task.task_type,
            state=task.state,
            start_time=task.start_time,
            end_time=task.end_time,
            exception=task.exception,
            task_submission_data=task.task_submission_data,
            nix_status=task.nix_status,
        )


# sent from frontend to controller

# none yet

# sent from controller to task runner


class TaskSubmission(BaseModel):
    id: uuid.UUID  # uuid
    data: "TaskSubmissionData" = Field(discriminator="type")

    @classmethod
    def from_orm_task(cls, task: Task) -> "TaskSubmission":
        return cls(id=task.id, data=task.task_submission_data)


TaskSubmissionData = Union[
    "DeployDevicesTaskSubmission",
    "DeployDeviceTaskSubmission",
    "ProjectFlakeUpdateTaskSubmission",
    "BuildProjectTaskSubmission",
    "BuildDeviceImageTaskSubmission",
    "SSHCommandTaskSubmission",
]


class TaskSubmissionDataWrapper(BaseModel):
    inner: TaskSubmissionData = Field(discriminator="type")


class DeployDeviceInformation(BaseModel):
    identifier: str
    host: str
    port: int
    username: str


# def warn_if_called_and_return_none():
#     import logging
#     logger = logging.getLogger(__name__)
#     logger.warning("Field default_factory for some key of SSHCommandTaskSubmission called, returning None")
#     return None
def warn_if_called_and_return_none(class_name: str, field_name: str):
    def inner():
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(
            f"Field default_factory for {class_name}.{field_name} called, returning None"
        )
        return None

    return inner


class DeployDevicesTaskSubmission(BaseModel):
    type: Literal["deploy_devices_task"] = "deploy_devices_task"
    devices: list[DeployDeviceInformation]
    project_path: str
    ssh_key_path: str
    known_hosts_path: str
    controller_ssh_pubkey: str | None = Field(
        default_factory=warn_if_called_and_return_none(
            "DeployDevicesTaskSubmission", "controller_ssh_pubkey"
        )
    )


class DeployDeviceTaskSubmission(BaseModel):
    type: Literal["deploy_device_task"] = "deploy_device_task"
    device: DeployDeviceInformation
    project_path: str
    ssh_key_path: str
    known_hosts_path: str
    controller_ssh_pubkey: str | None = Field(
        default_factory=warn_if_called_and_return_none(
            "DeployDeviceTaskSubmission", "controller_ssh_pubkey"
        )
    )
    parent_task_id: Optional[uuid.UUID] = None


class ProjectFlakeUpdateTaskSubmission(BaseModel):
    type: Literal["project_flake_update_task"] = "project_flake_update_task"
    project_path: str


class BuildProjectTaskSubmission(BaseModel):
    type: Literal["build_project_task"] = "build_project_task"
    project_path: str


class BuildDeviceImageTaskSubmission(BaseModel):
    type: Literal["build_device_image_task"] = "build_device_image_task"
    project_path: str
    device_identifier: str
    device_state: dict
    commit: str
    controller_ssh_pubkey: str | None = Field(
        default_factory=warn_if_called_and_return_none(
            "BuildDeviceImageTaskSubmission", "controller_ssh_pubkey"
        )
    )


class SSHCommandTaskSubmission(BaseModel):
    type: Literal["ssh_command_task"] = "ssh_command_task"
    target_user: str
    target_host: str
    target_port: int
    command: str
    ssh_key_path: str | None = Field(
        default_factory=warn_if_called_and_return_none(
            "SSHCommandTaskSubmission", "ssh_key_path"
        )
    )
    ssh_known_hosts_path: str | None = Field(
        default_factory=warn_if_called_and_return_none(
            "SSHCommandTaskSubmission", "ssh_known_hosts_path"
        )
    )


# sent from task runner to controller


class RunnerToControllerTaskUpdate(BaseModel):
    id: uuid.UUID  # uuid of the task
    update: "TaskUpdate" = Field(discriminator="type")


TaskUpdate = Union[
    "TaskPickedUpdate",
    "TaskRejectedUpdate",
    "TaskStdOutErrUpdate",
    "TaskNixStatusUpdate",
    "TaskCompletedUpdate",
    "TaskFailedUpdate",
    "CommandRunUpdate",
    "ImageBuiltUpdate",
]


class TaskPickedUpdate(BaseModel):
    type: Literal["task_picked"] = "task_picked"


class TaskRejectedUpdate(BaseModel):
    type: Literal["task_rejected"] = "task_rejected"
    reason: str


class TaskStdOutErrUpdate(BaseModel):
    type: Literal["task_stdout_err"] = "task_stdout_err"
    stdoutb64: str  # base64 encoded
    stderrb64: str  # base64 encoded


class TaskNixStatusUpdate(BaseModel):
    type: Literal["task_nix_status"] = "task_nix_status"
    status: ParsedNixProcess


class TaskCompletedUpdate(BaseModel):
    type: Literal["task_completed"] = "task_completed"


class TaskFailedUpdate(BaseModel):
    type: Literal["task_failed"] = "task_failed"
    reason: str


class CommandRunUpdate(BaseModel):
    type: Literal["command_run"] = "command_run"
    args: list[str]
    env: Optional[dict[str, str]] = None
    cwd: Optional[str] = None


class ImageBuiltUpdate(BaseModel):
    type: Literal["image_built"] = "image_built"
    configuration_id: str
    configuration_commit: str
    token: str


class CancelTask(BaseModel):
    id: uuid.UUID


__all__ = [
    "TaskState",
    "Task",
    "NixProcessStatus",
    "TaskShort",
    "TaskSubmission",
    "TaskSubmissionData",
    "DeployDeviceInformation",
    "DeployDeviceTaskSubmission",
    "DeployDevicesTaskSubmission",
    "ProjectFlakeUpdateTaskSubmission",
    "BuildProjectTaskSubmission",
    "BuildDeviceImageTaskSubmission",
    "SSHCommandTaskSubmission",
    "RunnerToControllerTaskUpdate",
    "TaskUpdate",
    "TaskPickedUpdate",
    "TaskRejectedUpdate",
    "TaskStdOutErrUpdate",
    "TaskNixStatusUpdate",
    "TaskCompletedUpdate",
    "TaskFailedUpdate",
    "CommandRunUpdate",
    "ImageBuiltUpdate",
    "CancelTask",
]
