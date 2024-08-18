import asyncio
import logging
import os
import pathlib
import signal
import subprocess
import sys

logger = logging.getLogger(__name__)

import fastapi
import httpx
import psutil
from fastapi import APIRouter, FastAPI
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from thymis_controller.config import global_settings

FRONTEND_PORT = 33100


def is_reload_enabled():
    return "--reload" in sys.argv


def frontend_binary_path():
    return global_settings.FRONTEND_BINARY_PATH


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
                "--strictPort",
                "--clearScreen",
                "false",
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        else:
            self.process = await asyncio.create_subprocess_exec(
                frontend_binary_path(),
                env={"PORT": str(FRONTEND_PORT), "HOST": "127.0.0.1"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        # read stdout and stderr in background
        async def read_stream(stream: asyncio.StreamReader, level=logging.INFO):
            while self.process.returncode is None and not self.stopped:
                line = await stream.readline()
                if line:
                    logger.log(
                        level, "frontend process: %s", line.decode("utf-8").strip()
                    )
                await asyncio.sleep(0.001)

        # start threads
        asyncio.create_task(read_stream(self.process.stdout))
        asyncio.create_task(read_stream(self.process.stderr, level=logging.ERROR))

    async def raise_if_terminated(self):
        return_code = await self.process.wait()
        if not self.stopped:
            self.stopped = True
            logger.error("frontend process terminated with code %s", return_code)
            await asyncio.sleep(0.1)
            os.kill(os.getpid(), signal.SIGINT)

    async def stop(self):
        if self.stopped:
            raise RuntimeError("frontend already stopped")
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
