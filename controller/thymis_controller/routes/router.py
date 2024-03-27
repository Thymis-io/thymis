import asyncio
import json
from typing import List
from thymis_controller.models.state import State
from fastapi import APIRouter, Depends, Request, BackgroundTasks, WebSocket
from fastapi.responses import FileResponse, RedirectResponse
from ..dependencies import get_or_init_state
from thymis_controller import models
from thymis_controller.crud import state
import subprocess
from urllib.parse import urljoin

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
    request: Request,
    background_tasks: BackgroundTasks,
    state: State = Depends(get_or_init_state),
):
    referer = request.headers.get("referer")
    # if something goes wrong, redirect to the referer
    try:
        image_path = await state.build_image_path(
            q=last_build_status, hostname=hostname
        )

        # return the image bytes
        return FileResponse(
            image_path,
            media_type="application/octet-stream",
            filename=f"thymis-{hostname}.img",
        )
    except Exception as e:
        err_msg = f"Error: {e}"
        import traceback

        traceback.print_exc()
        new_url = urljoin(referer, f"?error={err_msg}")
        return RedirectResponse(new_url)


@router.get("/history")
def get_history(state: State = Depends(get_or_init_state)):
    return state.get_history()


@router.post("/action/update")
async def update(
    background_tasks: BackgroundTasks, state: State = Depends(get_or_init_state)
):
    background_tasks.add_task(state.update, last_build_status)
    return {"message": "update started"}
