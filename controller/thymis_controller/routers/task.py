import uuid

from fastapi import APIRouter, WebSocket
from thymis_controller.dependencies import SessionAD, TaskControllerAD
from thymis_controller.task.controller import TaskController

router = APIRouter()

global_task_controller = None


@router.websocket("/task_status")
async def task_status(websocket: WebSocket, task_controller: TaskControllerAD):
    await task_controller.subscribe_ui(websocket)


@router.get("/tasks")
async def get_tasks(task_controller: TaskControllerAD, session: SessionAD):
    return task_controller.get_tasks(session)


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: uuid.UUID, task_controller: TaskControllerAD, db_session: SessionAD
):
    return task_controller.get_task(task_id, db_session)


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: uuid.UUID):
    await global_task_controller.cancel_task(task_id)
    return {"message": "Task cancelled"}


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: uuid.UUID):
    await global_task_controller.retry_task(task_id)
    return {"message": "Task retried"}


@router.post("/tasks/{task_id}/run_immediately")
async def run_immediately(task_id: uuid.UUID):
    await global_task_controller.run_immediately(task_id)
    return {"message": "Task run immediately"}
