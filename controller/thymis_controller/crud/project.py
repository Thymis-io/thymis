import json
from pathlib import Path
from thymis_controller.models.state import State
import os


class Project:
    def __init__(self, path):
        self.path = path

    def is_initialized(self):
        return Path(self.path).is_dir() and (Path(self.path) / "state.json").is_file()

    def initialize(self):
        Path(self.path).mkdir(exist_ok=True)
        # TODO git reop init - git config user and email
        state = State(
            version="0.0.1",
            repositories={},
            tags=[],
            devices=[],
        )
        self.update_state(state.model_dump())

    def load_state_from_file(self):
        with open(Path(self.path) / "state.json", "r", encoding="utf-8") as f:
            state_dict = json.load(f)
        state = State.load_from_dict(state_dict)
        state.set_repositories_in_python_path(self.path)
        return state

    def update_state(self, state):
        old_state = self.load_state_from_file()
        try:
            state = State.load_from_dict(state)
            state.save(self.path)
            state.write_nix(self.path)
        except Exception as e:
            old_state.save(self.path)
            old_state.write_nix(self.path)
            raise e


REPO_PATH = os.getenv("REPO_PATH")
global_project = Project(REPO_PATH)
