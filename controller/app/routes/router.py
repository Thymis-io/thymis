from typing import List
from fastapi import APIRouter, Depends, Request
from ..dependencies import get_state
from app import models
from app.crud import state


router = APIRouter()


@router.get("/state")
def get_state(state=Depends(get_state)):
    return state


@router.get("/guistate")
def get_guistate():
    return ""


@router.patch("/state")
async def update_state(new_state: Request):
    converted = state.convert((await new_state.json()))
    state.save(converted)
    return state.load()
