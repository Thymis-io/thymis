import uuid

from fastapi import APIRouter, WebSocket
from thymis_controller.task import global_task_controller

router = APIRouter()


@router.websocket("/task_status")
async def task_status(websocket: WebSocket):
    await global_task_controller.connect(websocket)


@router.get("/tasks")
async def get_tasks():
    return global_task_controller.get_tasks()


@router.get("/tasks/{task_id}")
async def get_task(task_id: uuid.UUID):
    return global_task_controller.get_task(task_id)


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
