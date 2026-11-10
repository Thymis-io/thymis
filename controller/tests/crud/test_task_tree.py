from datetime import datetime, timedelta, timezone

from thymis_controller import crud

BASE_TIME = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _task(db_session, seconds, parent=None):
    return crud.task.create(
        db_session,
        submitted_time=BASE_TIME + timedelta(seconds=seconds),
        state="completed",
        task_type="build_project_task",
        user_session_id=None,
        task_submission_data={},
        parent_task_id=parent.id if parent else None,
    )


def test_tasks_page_over_top_level_tasks_with_all_subtasks(db_session):
    old_root = _task(db_session, 0)
    old_child = _task(db_session, 1, parent=old_root)
    new_root = _task(db_session, 10)
    child = _task(db_session, 11, parent=new_root)
    grandchild = _task(db_session, 12, parent=child)

    assert crud.task.get_task_count(db_session) == 2

    first_page = crud.task.get_tasks_short(db_session, limit=1)
    assert {task.id for task in first_page} == {new_root.id, child.id, grandchild.id}
    assert {task.id: task.parent_task_id for task in first_page}[
        grandchild.id
    ] == child.id

    second_page = crud.task.get_tasks_short(db_session, limit=1, offset=1)
    assert {task.id for task in second_page} == {old_root.id, old_child.id}
