import traceback
import uuid

from fastapi import APIRouter, Response, WebSocket
from thymis_controller.dependencies import ProjectAD, SessionAD, TaskControllerAD
from thymis_controller.routers.frontend import is_running_in_playwright

router = APIRouter()


@router.websocket("/task_status")
async def task_status(websocket: WebSocket, task_controller: TaskControllerAD):
    await task_controller.subscribe_ui(websocket)


@router.get("/tasks")
async def get_tasks(
    task_controller: TaskControllerAD,
    session: SessionAD,
    response: Response,
    limit: int = 100,
    offset: int = 0,
):
    response.headers["total-count"] = str(task_controller.get_task_count(session))
    return task_controller.get_tasks(session, limit, offset)


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: uuid.UUID, task_controller: TaskControllerAD, db_session: SessionAD
):
    try:
        return task_controller.get_task(task_id, db_session)
    except ValueError:
        traceback.print_exc()
        return Response(
            content=f"Task with id {task_id} not found",
            status_code=404,
        )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_controller: TaskControllerAD, task_id: uuid.UUID):
    task_controller.cancel_task(task_id)
    return {"message": "Task cancelled"}


@router.post("/tasks/{task_id}/retry")
async def retry_task(
    task_controller: TaskControllerAD, db_session: SessionAD, task_id: uuid.UUID
):
    task_controller.retry_task(task_id, db_session)
    return {"message": "Task retried"}


@router.post("/tasks/delete_all")
async def delete_all_tasks(
    task_controller: TaskControllerAD, db_session: SessionAD, project: ProjectAD
):
    if is_running_in_playwright():
        task_controller.delete_all_tasks(db_session)
        project.clear_history(db_session)
        return {"message": "All tasks deleted"}
    else:
        return Response(status_code=403)
