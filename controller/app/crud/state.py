import json
from pydoc import locate
from pathlib import Path
from app import models


state_path = "./state.json"


def get_type_identifier(module):
    return f"{module.__class__.__module__}.{module.__class__.__name__}"


def is_initalized():
    return Path(state_path).is_file()


def initalize():
    save([
        models.Module(name="M1"),
        models.Minio(name="Minio Module"),
    ])


def load():
    with open(state_path, "r") as f:
        raw_state = json.load(f)

    state = []
    for entry in raw_state["modules"]:
        loaded_class = locate(entry["__type__"])
        state.append(loaded_class(**entry))
    
    return state


def save(state):
    with open(state_path, "w+") as f:
        json.dump({
                "version": "0.1.0",
                "modules": [{"__type__": get_type_identifier(module), **module.model_dump()} for module in state],
            }, f, indent=2)
