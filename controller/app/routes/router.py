from typing import List
from fastapi import APIRouter, Depends
from ..dependencies import get_state
from app import models

router = APIRouter()


@router.get("/state", response_model=List[models.Module])
def get_state(state=Depends(get_state)):
    return state


@router.get("/guistate")
def get_guistate():
    return ""
