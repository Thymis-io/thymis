import asyncio
from typing import List
from app.models.state import State
from fastapi import APIRouter, Depends, Request, BackgroundTasks
from ..dependencies import get_or_init_state
from app import models
from app.crud import state


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


last_build_status = asyncio.Queue(maxsize=1)


@router.post("/action/build")
def build_nix(
    background_tasks: BackgroundTasks, state: State = Depends(get_or_init_state)
):
    # runs a nix command to build the flake
    background_tasks.add_task(state.build_nix, last_build_status)
    # now build_nix: type: BackgroundTasks -> None

    return {"message": "nix build started"}


@router.get("/build_status")
def get_build_status():
    if last_build_status.empty():
        return {"status": "no build running"}

    # peek
    return {"status": last_build_status._queue[0]}


@router.post("/action/deploy")
def deploy(
    background_tasks: BackgroundTasks, state: State = Depends(get_or_init_state)
):
    # runs a nix command to deploy the flake
    background_tasks.add_task(state.deploy, last_build_status)

    return {"message": "nix deploy started"}
