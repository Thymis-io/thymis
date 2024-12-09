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
    display_name,
    type,
    task_submission_data,
    parent_task_id,
    children,
    process_program,
    process_args,
    process_env,
):
    task = db_models.Task(
        start_time=start_time,
        state=state,
        display_name=display_name,
        type=type,
        task_submission_data=task_submission_data,
        parent_task_id=parent_task_id,
        children=children,
        process_program=process_program,
        process_args=process_args,
        process_env=process_env,
    )
    db_session.add(task)

    db_session.commit()

    return task


def get_tasks_short(db_session: Session):
    all_tasks = db_session.scalars(
        select(db_models.Task).options(
            load_only(
                db_models.Task.id,
                db_models.Task.type,
                db_models.Task.display_name,
                db_models.Task.state,
                db_models.Task.start_time,
                db_models.Task.end_time,
                db_models.Task.exception,
                db_models.Task.task_submission_data,
            )
        )
    ).all()

    return [
        TaskShort(
            id=task.id,
            type=task.type,
            display_name=task.display_name,
            state=task.state,
            start_time=task.start_time,
            end_time=task.end_time,
            exception=task.exception,
            data=task.task_submission_data,
        )
        for task in all_tasks
    ]
