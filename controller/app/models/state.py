from typing import List, Optional
from pydantic import BaseModel, SerializeAsAny
from app import models
import os
from jinja2 import Environment, PackageLoader
import pathlib

env = Environment(
    loader=PackageLoader("app", "models"),
)

ALL_MODULES = [
    models.Module,
    models.Minio,
    models.Thymis,
]


class State(BaseModel):
    version: str
    modules: List[SerializeAsAny[models.Module]]

    def write_nix(self, path: os.PathLike):
        path = pathlib.Path(path)
        # write a flake.nix
        with open(path / "flake.nix", "w+") as f:
            f.write(env.get_template("flake.nix.j2").render(state=self))
        # create modules folder if not exists
        modules_path = path / "modules"
        modules_path.mkdir(exist_ok=True)
        for module in modules_path.glob("*.nix"):
            module.unlink()
        # write modules
        for module in self.modules:
            module.write_nix(modules_path, env)

    def available_modules(self):
        # return all modules that are not already included in the state
        out = []
        for module in ALL_MODULES:
            if module not in [type(m) for m in self.modules]:
                out.append(module())
        return out

    @classmethod
    def load_from_dict(cls, d):
        return cls(
            version=d["version"],
            modules=[models.Module.from_dict(module) for module in d["modules"]],
        )

    def save(self, path: os.PathLike = "./"):
        path = os.path.join(path, "state.json")
        with open(path, "w+") as f:
            f.write(self.model_dump_json(indent=2))
