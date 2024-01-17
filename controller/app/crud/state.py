import json
from pydoc import locate
from pathlib import Path
from app import models
from app.models.state import State


REPO_PATH: str = "/home/elikoga/Dev/thymis/testrepo"


def get_type_identifier(module):
    return f"{module.__class__.__module__}.{module.__class__.__name__}"


def is_initialized():
    return Path(REPO_PATH).is_dir() and (Path(REPO_PATH) / "state.json").is_file()
    # return False


def initialize():
    Path(REPO_PATH).mkdir(exist_ok=True)
    state = State(
        version="0.0.1",
        modules=[
            # models.Module(name="M1"),
            # models.Minio(name="Minio Module"),
            models.Thymis(name="Thymis Module"),
        ],
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
