from typing import List
from app.models.state import State
from fastapi import APIRouter, Depends, Request
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
