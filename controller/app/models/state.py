import asyncio
from typing import List, Optional
from pydantic import BaseModel, SerializeAsAny
from app import models
import os
from jinja2 import Environment, PackageLoader
import pathlib
from app.models.modules import ALL_MODULES

REPO_PATH = os.getenv("REPO_PATH")

env = Environment(
    loader=PackageLoader("app", "models"),
)

HOST_PRIORITY = 100


def del_path(path):
    if path.is_dir():
        for p in path.iterdir():
            del_path(p)
        path.rmdir()
    else:
        path.unlink()


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
        del_path(modules_path)
        modules_path.mkdir(exist_ok=True)
        # create and empty hosts, tags folder
        del_path(path / "hosts")
        del_path(path / "tags")
        (path / "hosts").mkdir(exist_ok=True)
        (path / "tags").mkdir(exist_ok=True)
        # for each host create its own folder
        for device in self.devices:
            # assert: hostname cannot be empty
            assert device.hostname, "hostname cannot be empty"
            device_path = path / "hosts" / device.hostname
            device_path.mkdir(exist_ok=True)
            # write its modules
            for module_settings in device.modules:
                # module holds settings right now.
                module = next(
                    m
                    for m in self.available_modules()
                    if m.type == module_settings.type
                )
                module.write_nix(device_path, module_settings, HOST_PRIORITY)
        # for each tag create its own folder
        for tag in self.tags:
            tag_path = path / "tags" / tag.name
            tag_path.mkdir(exist_ok=True)
            # write its modules
            for module_settings in tag.modules:
                # module holds settings right now.
                module = next(
                    m
                    for m in self.available_modules()
                    if m.type == module_settings.type
                )
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

    def repo_dir(self):
        return REPO_PATH

    async def build_nix(self, q: List):
        # runs a nix command to build the flake
        # async run commands using asyncio.subprocess
        # we will run
        # nix build REPO_PATH#thymis --out-link /tmp/thymis
        cmd = f"nix build {self.repo_dir()}#thymis --out-link /tmp/thymis"

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            q[0] = {
                "status": "failed",
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
            }

        q[0] = {
            "status": "success",
            "stdout": stdout.decode("utf-8"),
            "stderr": stderr.decode("utf-8"),
        }

    async def deploy(self, q: List):
        # for each device in the state
        # runs a command to deploy the flake

        # nixos-rebuild --flake REPO_PATH#thymis-devices.<device_name> switch --target-host <hostname>
        for device in self.devices:
            cmd = f"nixos-rebuild --flake {self.repo_dir()}#{device.hostname} switch --target-host {device.hostname}"

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                q[0] = {
                    "status": "failed",
                    "stdout": stdout.decode("utf-8"),
                    "stderr": stderr.decode("utf-8"),
                }
                return

            q[0] = {
                "status": "success",
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
            }
