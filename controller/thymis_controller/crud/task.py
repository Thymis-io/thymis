import os
import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session, load_only, selectinload
from thymis_controller import db_models
from thymis_controller.models.task import TaskShort, TaskState


def create(
    db_session: Session,
    submitted_time: datetime,
    state: TaskState,
    task_type: str,
    user_session_id: uuid.UUID,
    task_submission_data: dict,
    parent_task_id: uuid.UUID,
):
    id = uuid.uuid4()
    task = db_models.Task(
        id=id,
        submitted_time=submitted_time,
        state=state,
        task_type=task_type,
        user_session_id=user_session_id,
        task_submission_data=task_submission_data,
        parent_task_id=parent_task_id,
    )
    db_session.add(task)

    db_session.commit()

    return task


def _short_task_select():
    return select(db_models.Task).options(
        load_only(
            db_models.Task.id,
            db_models.Task.task_type,
            db_models.Task.state,
            db_models.Task.submitted_time,
            db_models.Task.start_time,
            db_models.Task.end_time,
            db_models.Task.exception,
            db_models.Task.task_submission_data,
            db_models.Task.parent_task_id,
        ),
        selectinload(db_models.Task.processes).load_only(
            db_models.TaskProcess.nix_status
        ),
    )


def get_tasks_short(
    db_session: Session, limit: int = 100, offset: int = 0
) -> list[TaskShort]:
    """Pages over top-level tasks, newest first, each with all its descendants."""
    roots = db_session.scalars(
        _short_task_select()
        .where(db_models.Task.parent_task_id.is_(None))
        .order_by(db_models.Task.submitted_time.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [
        *(TaskShort.from_orm_task(root) for root in roots),
        *get_subtasks(db_session, [root.id for root in roots]),
    ]


def get_task_count(db_session: Session):
    """Counts top-level tasks, the unit get_tasks_short pages over."""
    return (
        db_session.query(db_models.Task)
        .filter(db_models.Task.parent_task_id.is_(None))
        .count()
    )


def get_subtasks(db_session: Session, task_ids: list[uuid.UUID]) -> list[TaskShort]:
    """All tasks below `task_ids`; each is visited once, so cycles end."""
    seen = set(task_ids)
    subtasks = []
    while task_ids:
        children = [
            child
            for child in db_session.scalars(
                _short_task_select().where(db_models.Task.parent_task_id.in_(task_ids))
            )
            if child.id not in seen
        ]
        seen.update(child.id for child in children)
        subtasks.extend(TaskShort.from_orm_task(child) for child in children)
        task_ids = [child.id for child in children]
    return subtasks


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
        query = query.filter(db_models.Task.submitted_time >= from_date)
    if to_date:
        query = query.filter(db_models.Task.submitted_time <= to_date)
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


def child_task_states(db_session: Session, parent_task_id: uuid.UUID) -> set[str]:
    """States of the children a composite task waits on."""
    return set(
        db_session.scalars(
            select(db_models.Task.state).where(
                db_models.Task.parent_task_id == parent_task_id
            )
        )
    )


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
