import json
from typing import List
import pydantic
from pathlib import Path
from app import models
from pydoc import locate

def get_type_identifier(module):
    return f"{module.__class__.__module__}.{module.__class__.__name__}"

def get_state():
    if not Path("./state.json").is_file():
        init_state = [
            models.Module(name="M1"),
        ]

        with open("./state.json", "w+") as f:
            json.dump([{'__type__': get_type_identifier(module), **module.model_dump()} for module in init_state], f)

    with open("./state.json", "r") as f:
        raw_state = json.load(f)

    state = []
    for entry in raw_state:
        loaded_class = locate(entry["__type__"])
        state.append(loaded_class(**entry))
    
    return state
