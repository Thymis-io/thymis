import json
from pathlib import Path

from . import models

def get_state():
    if not Path("./state.json").is_file():
        return [
            models.Module(name="M1"),
        ]

    with open("./state.json", "r") as f:
        return json.load(f)
