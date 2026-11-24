"""GET /api/tasks/{id}/subtasks returns a task's descendants as a flat list."""

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


def test_subtasks_returns_every_level(test_client, db_session):
    root = _task(db_session, 0)
    child = _task(db_session, 1, parent=root)
    grandchild = _task(db_session, 2, parent=child)
    great_grandchild = _task(db_session, 3, parent=grandchild)
    _task(db_session, 4)  # unrelated

    response = test_client.get(f"/api/tasks/{root.id}/subtasks")

    assert response.status_code == 200
    by_id = {task["id"]: task["parent_task_id"] for task in response.json()}
    assert by_id == {
        str(child.id): str(root.id),
        str(grandchild.id): str(child.id),
        str(great_grandchild.id): str(grandchild.id),
    }


def test_subtasks_terminate_on_a_cycle(test_client, db_session):
    a, b, c = (_task(db_session, i) for i in range(3))
    a.parent_task_id, b.parent_task_id, c.parent_task_id = c.id, a.id, b.id
    db_session.commit()

    response = test_client.get(f"/api/tasks/{a.id}/subtasks")

    assert response.status_code == 200
    assert sorted(task["id"] for task in response.json()) == sorted(
        [str(b.id), str(c.id)]
    )
