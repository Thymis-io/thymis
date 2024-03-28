import json
from pydoc import locate
from pathlib import Path
from thymis_controller.models.state import State
import os

REPO_PATH = os.getenv("REPO_PATH")


def get_type_identifier(module):
    return f"{module.__class__.__module__}.{module.__class__.__name__}"


def is_initialized():
    return Path(REPO_PATH).is_dir() and (Path(REPO_PATH) / "state.json").is_file()
    # return False


def initialize():
    Path(REPO_PATH).mkdir(exist_ok=True)
    # TODO git reop init - git config user and email
    state = State(
        version="0.0.1",
        tags=[],
        devices=[],
    )
    update(state.model_dump())


def load_from_file():
    with open(Path(REPO_PATH) / "state.json", "r", encoding="utf-8") as f:
        state_dict = json.load(f)
    return State.load_from_dict(state_dict)


def update(d):
    state = State.load_from_dict(d)
    state.save(REPO_PATH)
    state.write_nix(REPO_PATH)
