import datetime
import uuid
from typing import TYPE_CHECKING, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, JsonValue, ValidationError
from thymis_agent import agent
from thymis_controller.nix.log_parse import ParsedNixProcess

type TaskState = Literal["pending", "running", "completed", "failed"]

if TYPE_CHECKING:
    import thymis_controller.db_models as db_models

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
    task_submission_data: Optional["TaskSubmissionData"] = None
    task_submission_data_raw: Optional[JsonValue]

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

    @classmethod
    def from_orm_task(cls, task: "db_models.Task") -> "Task":
        try:
            # first check wether TaskSubmissionData is still parseable, if not, return None for task_submission_data
            submission_data = TaskSubmissionDataWrapper(
                inner=task.task_submission_data
            ).inner
            submission_data_raw = None
        except ValidationError:
            submission_data = None
            submission_data_raw = task.task_submission_data
        return cls(
            id=task.id,
            start_time=task.start_time,
            end_time=task.end_time,
            state=task.state,
            exception=task.exception,
            task_type=task.task_type,
            task_submission_data=submission_data,
            task_submission_data_raw=submission_data_raw,
            parent_task_id=task.parent_task_id,
            children=task.children,
            process_program=task.process_program,
            process_args=task.process_args,
            process_env=task.process_env,
            process_stdout=task.process_stdout,
            process_stderr=task.process_stderr,
            nix_status=task.nix_status,
            nix_errors=task.nix_errors,
            nix_files_linked=task.nix_files_linked,
            nix_bytes_linked=task.nix_bytes_linked,
            nix_corrupted_paths=task.nix_corrupted_paths,
            nix_untrusted_paths=task.nix_untrusted_paths,
            nix_error_logs=task.nix_error_logs,
            nix_warning_logs=task.nix_warning_logs,
            nix_notice_logs=task.nix_notice_logs,
            nix_info_logs=task.nix_info_logs,
        )


class TaskShort(BaseModel):
    id: uuid.UUID  # uuid
    task_type: str
    state: TaskState
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    exception: Optional[str]
    task_submission_data: Optional["TaskSubmissionData"]
    nix_status: Optional[NixProcessStatus]

    @classmethod
    def from_orm_task(cls, task: "db_models.Task") -> "TaskShort":
        try:
            # first check wether TaskSubmissionData is still parseable, if not, return None for task_submission_data
            submission_data = TaskSubmissionDataWrapper(
                inner=task.task_submission_data
            ).inner
        except ValidationError:
            submission_data = None
        return cls(
            id=task.id,
            task_type=task.task_type,
            state=task.state,
            start_time=task.start_time,
            end_time=task.end_time,
            exception=task.exception,
            task_submission_data=submission_data,
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
    "RunNixOSVMTaskSubmission",
]


class TaskSubmissionDataWrapper(BaseModel):
    inner: TaskSubmissionData = Field(discriminator="type")


class DeployDeviceInformation(BaseModel):
    identifier: str
    deployment_info_id: uuid.UUID
    deployment_public_key: str
    secrets: list[agent.SecretForDevice] = []


class DeployDevicesTaskSubmission(BaseModel):
    type: Literal["deploy_devices_task"] = "deploy_devices_task"
    devices: list[DeployDeviceInformation]
    project_path: str
    ssh_key_path: str
    known_hosts_path: str
    controller_ssh_pubkey: str
    config_commit: str


class DeployDeviceTaskSubmission(BaseModel):
    type: Literal["deploy_device_task"] = "deploy_device_task"
    device: DeployDeviceInformation
    project_path: str
    ssh_key_path: str
    known_hosts_path: str
    controller_ssh_pubkey: str
    controller_access_client_endpoint: str
    access_client_token: str
    config_commit: str
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
    configuration_id: str
    config_state: dict
    commit: str
    controller_ssh_pubkey: str
    secrets: list[agent.SecretForDevice] = []


class SSHCommandTaskSubmission(BaseModel):
    type: Literal["ssh_command_task"] = "ssh_command_task"
    controller_access_client_endpoint: str
    deployment_info_id: uuid.UUID
    access_client_token: str
    deployment_public_key: str
    ssh_key_path: str
    target_user: str
    target_port: int
    command: str


class RunNixOSVMTaskSubmission(BaseModel):
    type: Literal["run_nixos_vm_task"] = "run_nixos_vm_task"
    configuration_id: str
    project_path: str
    parent_task_id: Optional[uuid.UUID] = None


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
    "AgentShouldSwitchToNewConfigurationUpdate",
    "WorkerRequestsSecretsUpdate",
    "AgentShouldReceiveNewSecretsUpdate",
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
    image_format: str
    configuration_id: str
    configuration_commit: str
    token: str


class AgentShouldSwitchToNewConfigurationUpdate(BaseModel):
    type: Literal[
        "agent_should_switch_to_new_configuration"
    ] = "agent_should_switch_to_new_configuration"
    path_to_configuration: str
    deployment_info_id: uuid.UUID
    config_commit: str


class AgentSwitchedToNewConfigurationUpdate(BaseModel):
    type: Literal[
        "agent_switched_to_new_configuration"
    ] = "agent_switched_to_new_configuration"
    success: bool
    reason: Optional[str]


class WorkerRequestsSecretsUpdate(BaseModel):
    type: Literal["worker_requests_secrets"] = "worker_requests_secrets"
    secret_ids: list[uuid.UUID]
    target_recipient_token: str


class AgentShouldReceiveNewSecretsUpdate(BaseModel):
    type: Literal[
        "agent_should_receive_new_secrets"
    ] = "agent_should_receive_new_secrets"
    secrets: list[agent.SecretForDevice]
    target_deployment_info_id: uuid.UUID
    target_recipient_ssh_pubkey: str


# sent from controller to task runner
class ControllerToRunnerTaskUpdate(BaseModel):
    inner: Union[
        "CancelTask",
        "AgentSwitchToNewConfigurationResult",
        "AgentGotNewSecretsResult",
        "SecretsResult",
    ] = Field(discriminator="kind")


class CancelTask(BaseModel):
    kind: Literal["cancel_task"] = "cancel_task"
    id: uuid.UUID


class AgentSwitchToNewConfigurationResult(BaseModel):
    kind: Literal[
        "agent_switch_to_new_configuration_result"
    ] = "agent_switch_to_new_configuration_result"
    success: bool
    stdout: str
    stderr: str


class AgentGotNewSecretsResult(BaseModel):
    kind: Literal["agent_got_new_secrets_result"] = "agent_got_new_secrets_result"
    success: bool


class SecretsResult(BaseModel):
    kind: Literal["secrets_result"] = "secrets_result"
    secrets: dict[uuid.UUID, bytes]


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
    "AgentShouldSwitchToNewConfigurationUpdate",
    "ControllerToRunnerTaskUpdate",
    "CancelTask",
    "AgentSwitchToNewConfigurationResult",
    "WorkerRequestsSecretsUpdate",
    "AgentShouldReceiveNewSecretsUpdate",
    "AgentGotNewSecretsResult",
    "SecretsResult",
]
