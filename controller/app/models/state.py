from typing import List, Optional
from pydantic import BaseModel, SerializeAsAny
from app import models
import os
from jinja2 import Environment, PackageLoader
import pathlib

env = Environment(
    loader=PackageLoader("app", "models"),
)

ALL_MODULES: List[models.Module] = [
    models.Module(),
    models.Minio(),
    models.Thymis(),
]

HOST_PRIORITY = 100


class State(BaseModel):
    version: str
    modules: List[SerializeAsAny[models.Module]]
    tags: List[models.Tag]
    devices: List[models.Device]

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
        # create and empty hosts, tags folder
        (path / "hosts").mkdir(exist_ok=True)
        (path / "tags").mkdir(exist_ok=True)
        # empty hosts, tags folder
        for module in (path / "hosts").glob("*.nix"):
            module.unlink()
        for module in (path / "tags").glob("*.nix"):
            module.unlink()
        # for each host create its own folder
        for device in self.devices:
            device_path = path / "hosts" / device.hostname
            device_path.mkdir(exist_ok=True)
            # write its modules
            for module_settings in device.modules:
                # module holds settings right now.
                module = next(m for m in self.available_modules() if m.type == module_settings.type)
                module.write_nix(device_path, module_settings, HOST_PRIORITY)
        # for each tag create its own folder
        for tag in self.tags:
            tag_path = path / "tags" / tag.name
            tag_path.mkdir(exist_ok=True)
            # write its modules
            for module_settings in tag.modules:
                # module holds settings right now.
                module = next(m for m in self.available_modules() if m.type == module_settings.type)
                module.write_nix(tag_path, module_settings, tag.priority)

    def available_modules(self):
        return ALL_MODULES

    @classmethod
    def load_from_dict(cls, d):
        return cls(
            version=d["version"],
            modules=[models.Module.from_dict(module) for module in d["modules"]],
            tags=d["tags"] if "tags" in d else [],
            devices=d["devices"] if "devices" in d else [],
        )

    def save(self, path: os.PathLike = "./"):
        path = os.path.join(path, "state.json")
        with open(path, "w+", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
