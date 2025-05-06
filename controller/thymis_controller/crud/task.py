import os
import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, load_only
from thymis_controller import db_models
from thymis_controller.models.task import TaskShort


def create(
    db_session: Session,
    start_time,
    state,
    task_type,
    user_session_id,
    task_submission_data,
    parent_task_id,
):
    id = uuid.uuid4()
    task = db_models.Task(
        id=id,
        start_time=start_time,
        state=state,
        task_type=task_type,
        user_session_id=user_session_id,
        task_submission_data=task_submission_data,
        parent_task_id=parent_task_id,
    )
    db_session.add(task)

    db_session.commit()

    return task


def get_tasks_short(db_session: Session, limit: int = 100, offset: int = 0):
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
                db_models.Task.nix_status,
            )
        )
        .order_by(db_models.Task.start_time.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return [TaskShort.from_orm_task(task) for task in all_tasks]


def get_task_count(db_session: Session):
    return db_session.query(db_models.Task).count()


def get_task_by_id(db_session, task_id: uuid.UUID) -> db_models.Task:
    task = db_session.query(db_models.Task).filter(db_models.Task.id == task_id).first()
    if task is None:
        raise ValueError(f"Task with id {task_id} not found")
    return task


def get_tasks_with_state(
    db_session: Session,
    state: Literal["pending", "running", "completed", "failed"],
    from_date: datetime = None,
    to_date: datetime = None,
) -> db_models.Task:
    query = db_session.query(db_models.Task).filter(db_models.Task.state == state)
    if from_date:
        query = query.filter(db_models.Task.start_time >= from_date)
    if to_date:
        query = query.filter(db_models.Task.start_time <= to_date)
    return query.all()


def fail_running_tasks(db_session):
    # runs on startup, fails any tasks that were running when the controller was last shut down
    running_tasks = (
        db_session.query(db_models.Task).filter(db_models.Task.state == "running").all()
    )
    for task in running_tasks:
        task.state = "failed"
        task.add_exception("Task was running when controller was shut down")
    db_session.commit()
    return len(running_tasks)


def child_task_states(db_session, tasks: list[uuid.UUID]) -> set[str]:
    tasks = db_session.query(db_models.Task).filter(db_models.Task.id.in_(tasks)).all()
    return set(task.state for task in tasks)


if "RUNNING_IN_PLAYWRIGHT" in os.environ:

    def delete_all_tasks(db_session: Session):
        db_session.query(db_models.Task).delete()
        db_session.commit()


def get_all_tasks(db_session: Session):
    return db_session.query(db_models.Task).all()


def get_all_alive_tasks(db_session: Session):
    # means that the task is not in any of the final states
    # final states are: failed, completed
    return (
        db_session.query(db_models.Task)
        .filter(db_models.Task.state.not_in(["failed", "completed"]))
        .all()
    )
