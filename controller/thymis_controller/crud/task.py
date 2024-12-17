import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, load_only
from thymis_controller import db_models
from thymis_controller.models.task import TaskShort

# class Task(Base):
#     __tablename__ = "tasks"

#     id = Column(Uuid(as_uuid=True), primary_key=True, index=True)
#     start_time = Column(DateTime, nullable=False)
#     end_time = Column(DateTime, nullable=True)
#     state = Column(String(50), nullable=False)
#     display_name = Column(String(255), nullable=False)
#     exception = Column(Text, nullable=True)
#     type = Column(String(50), nullable=False)
#     task_submission_data = Column(JSON, nullable=True)  # New field for submission data

#     # Composite Task Fields
#     parent_task_id = Column(Uuid(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
#     children = Column(JSON, nullable=True)

#     # Unified Process Fields
#     process_program = Column(String(255), nullable=True)
#     process_args = Column(JSON, nullable=True)
#     process_env = Column(JSON, nullable=True)
#     process_stdout = Column(Text, nullable=True)
#     process_stderr = Column(Text, nullable=True)

#     # Nix-Specific Extensions
#     nix_status = Column(JSON, nullable=True)
#     nix_files_linked = Column(Integer, nullable=True)
#     nix_bytes_linked = Column(BigInteger, nullable=True)
#     nix_corrupted_paths = Column(Integer, nullable=True)
#     nix_untrusted_paths = Column(Integer, nullable=True)
#     nix_errors = Column(JSON, nullable=True)

#     nix_warnings = Column(JSON, nullable=True)
#     nix_notices = Column(JSON, nullable=True)
#     nix_infos = Column(JSON, nullable=True)


def create(
    db_session: Session,
    start_time,
    state,
    task_type,
    task_submission_data,
    parent_task_id,
):
    id = uuid.uuid4()
    task = db_models.Task(
        id=id,
        start_time=start_time,
        state=state,
        task_type=task_type,
        task_submission_data=task_submission_data,
        parent_task_id=parent_task_id,
    )
    db_session.add(task)

    db_session.commit()

    return task


def get_tasks_short(db_session: Session, limit: int = 100):
    all_tasks = db_session.scalars(
        select(db_models.Task)
        .options(
            load_only(
                db_models.Task.id,
                db_models.Task.task_type,
                db_models.Task.state,
                db_models.Task.start_time,
                db_models.Task.end_time,
                db_models.Task.exception,
                db_models.Task.task_submission_data,
            )
        )
        .limit(limit)
    ).all()

    return [TaskShort.from_orm_task(task) for task in all_tasks]


def get_task_by_id(db_session, task_id: uuid.UUID) -> db_models.Task:
    task = db_session.query(db_models.Task).filter(db_models.Task.id == task_id).first()
    if task is None:
        raise ValueError(f"Task with id {task_id} not found")
    return task


def get_pending_tasks(db_session):
    return (
        db_session.query(db_models.Task).filter(db_models.Task.state == "pending").all()
    )


def fail_running_tasks(db_session):
    # runs on startup, fails any tasks that were running when the controller was last shut down
    running_tasks = (
        db_session.query(db_models.Task).filter(db_models.Task.state == "running").all()
    )
    for task in running_tasks:
        task.state = "failed"
        task.exception = "Task was running when controller was shut down"
    db_session.commit()
    return len(running_tasks)
