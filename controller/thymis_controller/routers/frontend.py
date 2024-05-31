import asyncio
import os
import pathlib
import subprocess
import sys
import traceback
from contextlib import asynccontextmanager

import fastapi
import httpx
import psutil
from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

FRONTEND_PORT = 33100


def is_reload_enabled():
    return "--reload" in sys.argv


def frontend_binary_path():
    return os.getenv("FRONTEND_BINARY")


class Frontend:
    def __init__(self):
        self.url = f"http://127.0.0.1:{FRONTEND_PORT}"
        self.process = None
        self.stopped = False

    async def run(self):
        if is_reload_enabled():
            frontend_path = (
                pathlib.Path(__file__).parent.parent.parent.parent / "frontend"
            )
            assert (
                frontend_path.exists()
            ), f"frontend path {frontend_path} does not exist"
            self.process = await asyncio.create_subprocess_exec(
                "npm",
                "run",
                "dev",
                "--",
                "--host=127.0.0.1",
                f"--port={FRONTEND_PORT}",
                cwd=frontend_path,
            )
        else:
            self.process = await asyncio.create_subprocess_exec(
                frontend_binary_path(),
                env={"PORT": str(FRONTEND_PORT), "HOST": "localhost"},
            )

    async def raise_if_terminated(self):
        return_code = await self.process.wait()
        if not self.stopped:
            self.stopped = True
            print(f"frontend process terminated with code {return_code}")
            traceback.print_stack()
            sys.exit(1)

    async def stop(self):
        if self.stopped:
            raise Exception("frontend already stopped")
        self.stopped = True
        process_pid = self.process.pid
        parent = psutil.Process(process_pid)
        for child in parent.children(recursive=True):
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
            await asyncio.sleep(0.1)
            if child.is_running():
                child.kill()
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        await asyncio.sleep(0.1)
        if parent.is_running():
            parent.kill()
        await self.process.wait()


frontend = Frontend()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("starting frontend")
    await frontend.run()
    print("frontend started1")
    asyncio.get_event_loop().create_task(frontend.raise_if_terminated())
    print("frontend started2")
    yield
    print("stopping frontend")
    await frontend.stop()
    print("frontend stopped")


client = httpx.AsyncClient(base_url=frontend.url)

router = APIRouter()


async def _reverse_proxy(request: fastapi.Request):
    url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
    rp_req = client.build_request(
        request.method,
        url,
        headers=request.headers.raw,
        content=request.stream(),
        timeout=None,
    )
    rp_resp = await client.send(rp_req, stream=True)
    return StreamingResponse(
        rp_resp.aiter_raw(),
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
        background=BackgroundTask(rp_resp.aclose),
    )


router.add_route(
    "/{path:path}",
    _reverse_proxy,
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
)
