import asyncio
import json
from typing import List
from app.models.state import State
from fastapi import APIRouter, Depends, Request, BackgroundTasks, WebSocket
from fastapi.responses import FileResponse
from ..dependencies import get_or_init_state
from app import models
from app.crud import state
import subprocess

router = APIRouter()


@router.get("/state")
def get_state(state: State = Depends(get_or_init_state)):
    return state


@router.get("/available_modules")
def get_available_modules(state: State = Depends(get_or_init_state)):
    return state.available_modules()


@router.patch("/state")
async def update_state(new_state: Request):
    return state.update(await new_state.json())


last_build_status = [None]


@router.post("/action/build")
def build_nix(
    background_tasks: BackgroundTasks, state: State = Depends(get_or_init_state)
):
    # runs a nix command to build the flake
    background_tasks.add_task(state.build_nix, last_build_status)
    # now build_nix: type: BackgroundTasks -> None

    return {"message": "nix build started"}


@router.websocket("/build_status")
async def build_status(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            if last_build_status[0] is None:
                await websocket.send_text(json.dumps({"status": "no build running"}))
            else:
                await websocket.send_text(json.dumps(last_build_status[0]))
            await asyncio.sleep(0.2)
    except:
        await websocket.close()


@router.post("/action/deploy")
def deploy(
    summary: str,
    background_tasks: BackgroundTasks,
    state: State = Depends(get_or_init_state),
):
    state.commit(summary)

    # runs a nix command to deploy the flake
    background_tasks.add_task(state.deploy, last_build_status)

    return {"message": "nix deploy started"}


@router.get("/action/build-download-image")
async def build_download_image(
    hostname: str,
    background_tasks: BackgroundTasks,
    state: State = Depends(get_or_init_state),
):
    image_path = await state.build_image_path(q=last_build_status, hostname=hostname)

    # return the image bytes
    return FileResponse(
        image_path,
        media_type="application/octet-stream",
        filename=f"thymis-{hostname}.img",
    )


@router.get("/history")
def get_history(state: State = Depends(get_or_init_state)):
    return state.get_history()
