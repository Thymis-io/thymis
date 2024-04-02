import asyncio
from typing import List, Optional
from pydantic import BaseModel, SerializeAsAny
from thymis_controller import models
import os
from jinja2 import Environment, PackageLoader
from git import Repo
import pathlib
from thymis_controller.migration.migrate import migrate
from thymis_controller.models.modules import ALL_MODULES
import subprocess

REPO_PATH = os.getenv("REPO_PATH")

env = Environment(
    loader=PackageLoader("thymis_controller", "models"),
)

HOST_PRIORITY = 100


def del_path(path: os.PathLike):
    if not path.exists():
        return

    if path.is_dir():
        for p in path.iterdir():
            del_path(p)
        path.rmdir()
    else:
        path.unlink()


other_procs = []


async def terminate_other_procs():
    for proc in other_procs:
        if proc.returncode is None:
            proc.terminate()
    # wait for them to terminate
    for proc in other_procs:
        await proc.wait()
    other_procs.clear()


class State(BaseModel):
    version: str
    tags: List[models.Tag]
    devices: List[models.Device]

    __q: List
    __stdout: bytearray
    __stderr: bytearray

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
            assert device.identifier, "identifier cannot be empty"
            device_path = path / "hosts" / device.identifier
            device_path.mkdir(exist_ok=True)
            # create a empty .gitignore file
            os.mknod(device_path / ".gitignore")
            # write its modules
            for module_settings in device.modules:
                # module holds settings right now.
                module = self.get_module_class_instance_by_type(module_settings.type)
                module.write_nix(device_path, module_settings, HOST_PRIORITY)
        # for each tag create its own folder
        for tag in self.tags:
            tag_path = path / "tags" / tag.displayName
            tag_path.mkdir(exist_ok=True)
            # create a empty .gitignore file
            os.mknod(tag_path / ".gitignore")
            # write its modules
            for module_settings in tag.modules:
                # module holds settings right now.
                module = self.get_module_class_instance_by_type(module_settings.type)
                module.write_nix(tag_path, module_settings, tag.priority)
        # run git add
        repo = Repo.init(self.repo_dir())
        repo.git.add(".")

    @classmethod
    def load_from_dict(cls, d):
        return cls(**migrate(d))

    def get_module_class_instance_by_type(self, module_type: str):
        for module in ALL_MODULES:
            if module.type == module_type:
                return module
        raise Exception(f"module with type {module_type} not found")

    def save(self, path: os.PathLike = "./"):
        path = os.path.join(path, "state.json")
        with open(path, "w+", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    def repo_dir(self):
        return REPO_PATH

    def update_status(self, status: str):
        self.__q[0] = {
            "status": status,
            "stdout": self.__stdout.decode("utf-8"),
            "stderr": self.__stderr.decode("utf-8"),
        }

    def commit(self, summary: str):
        repo = Repo.init(self.repo_dir())
        repo.git.add(".")

        try:
            # commit fails if there are no changes
            repo.git.commit("-m", summary)
            print("commited changes", summary)
        except:
            pass

    async def stream_reader(
        self,
        stream: asyncio.StreamReader | None,
        out: bytearray,
        status: str = "building",
    ):
        while True:
            line = await stream.readline()
            if not line:
                break
            out.extend(line)
            # self.update_status("building")
            self.update_status(status)

    async def build_nix(self, q: List):
        await terminate_other_procs()
        self.__q = q
        self.__stdout = bytearray()
        self.__stderr = bytearray()
        self.update_status("started building")

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

        other_procs.append(proc)
        asyncio.create_task(self.stream_reader(proc.stdout, self.__stdout))
        asyncio.create_task(self.stream_reader(proc.stderr, self.__stderr))

        r = await proc.wait()
        if r != 0:
            self.update_status("failed")
        else:
            self.update_status("success")

    async def build_image_path(self, q: List, identifier: str):
        await terminate_other_procs()
        self.__q = q
        self.__stdout = bytearray()
        self.__stderr = bytearray()
        self.update_status("started building")

        cmd = f"nix build '{self.repo_dir()}#nixosConfigurations.\"{identifier}\".config.formats.sd-card-image' --out-link /tmp/thymis-devices.{identifier}"

        print(f"running command: {cmd}")

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        other_procs.append(proc)
        asyncio.create_task(
            self.stream_reader(proc.stdout, self.__stdout, status="building image")
        )
        asyncio.create_task(
            self.stream_reader(proc.stderr, self.__stderr, status="building image")
        )

        r = await proc.wait()
        if proc.returncode != 0:
            raise Exception(f"failed to build image for {identifier}")
        return f"/tmp/thymis-devices.{identifier}"

    async def deploy(self, q: List):
        await terminate_other_procs()
        self.__q = q
        self.__stdout = bytearray()
        self.__stderr = bytearray()
        self.update_status("started deploying")

        # for each device in the state
        # runs a command to deploy the flake

        # nixos-rebuild --flake REPO_PATH#thymis-devices.<device_name> switch --target-host <hostname>
        for device in self.devices:
            cmd = f'nixos-rebuild --flake {self.repo_dir()}#"{device.identifier}" switch --target-host root@{device.targetHost}'

            proc = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    "NIX_SSHOPTS": f"-o StrictHostKeyChecking=accept-new",
                    "PATH": os.getenv("PATH"),
                },
            )

            other_procs.append(proc)
            asyncio.create_task(
                self.stream_reader(proc.stdout, self.__stdout, status="deploying")
            )
            asyncio.create_task(
                self.stream_reader(proc.stderr, self.__stderr, status="deploying")
            )

            r = await proc.wait()
            if r != 0:
                self.update_status("failed")
            else:
                self.update_status("success")

    def get_history(self):
        repo = Repo.init(self.repo_dir())
        return [
            {
                "message": commit.message,
                "author": commit.author.name,
                "date": commit.authored_datetime,
                "hash": commit.hexsha,
            }
            for commit in repo.iter_commits()
        ]

    async def update(self, q: List):
        await terminate_other_procs()
        self.__q = q
        self.__stdout = bytearray()
        self.__stderr = bytearray()
        self.update_status("started updating")

        # runs a nix command to update the flake
        # nix flake update
        cmd = f"nix flake update {self.repo_dir()}"

        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        other_procs.append(proc)
        asyncio.create_task(
            self.stream_reader(proc.stdout, self.__stdout, status="updating")
        )
        asyncio.create_task(
            self.stream_reader(proc.stderr, self.__stderr, status="updating")
        )

        r = await proc.wait()
        if r != 0:
            self.update_status("failed")
        else:
            self.update_status("success")
