import json
from typing import List
import pydantic
from pathlib import Path
from app import models


def get_state():
    if not Path("./state.json").is_file():
        init_state = [
            models.Module(name="M1"),
        ]

        with open("./state.json", "w+") as f:
            json.dump([module.model_dump() for module in init_state], f)

    with open("./state.json", "r") as f:
        raw_state = json.load(f)

    state = []
    for entry in raw_state:
        state.append(models.Module(**entry))
    
    return state
