from fastapi import APIRouter, Depends
from ..dependencies import get_state

router = APIRouter()


@router.get("/state")
def get_state(state=Depends(get_state)):
    return state


@router.get("/guistate")
def get_guistate():
    return ""
