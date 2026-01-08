import asyncio
import datetime
import logging
import os
import pathlib
import subprocess
import threading

from pydantic import BaseModel
from thymis_controller.notifications import NotificationManager
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class Commit(BaseModel):
    SHA: str
    SHA1: str
    message: str
    date: datetime.datetime
    author: str


class FileChange(BaseModel):
    path: str
    dir: str
    file: str
    diff: str


class RepoStatus(BaseModel):
    changes: list[FileChange]


class StateEventHandler(FileSystemEventHandler):
    def __init__(
        self, base_path: pathlib.Path, notification_manager: NotificationManager
    ):
        self.base_path = base_path
        self.notification_manager = notification_manager
        self.last_event = datetime.datetime.min
        self.event_loop = asyncio.get_event_loop()
        self.debounce_task = None
        self.paused = False
        self.lock = threading.Lock()
        self.update_paths = set()

    def on_any_event(self, event: FileSystemEvent) -> None:
        if self.paused:
            return
        if event.event_type not in ("modified", "created", "deleted"):
            return
        relative = pathlib.Path(event.src_path).relative_to(self.base_path)
        if str(relative).startswith(".git"):
            return
        with self.lock:
            self.update_paths.add("/api/repo_status")
            if str(relative).startswith("artifacts"):
                self.update_paths.add("/api/artifacts")
            else:
                self.update_paths.add("/api/state")

            if self.should_debounce():
                if not self.debounce_task or self.debounce_task.done():
                    self.debounce_task = self.event_loop.create_task(self.debounce())
            else:
                self.last_event = datetime.datetime.now()
                self.broadcast_update()

    def should_debounce(self):
        delta = datetime.datetime.now() - self.last_event
        return delta < datetime.timedelta(seconds=0.2)

    async def debounce(self):
        await asyncio.sleep(0.2)
        self.broadcast_update()

    def broadcast_update(self):
        if self.paused:
            return
        self.notification_manager.broadcast_invalidate_notification(self.update_paths)
        self.update_paths.clear()


class Repo:
    def __init__(self, path: pathlib.Path, notification_manager: NotificationManager):
        self.path = path
        self.notification_manager = notification_manager
        self.state_event_handler = None
        self.state_observer = None
        self.init()

    def start_file_watcher(self):
        self.state_event_handler = StateEventHandler(
            self.path, self.notification_manager
        )
        self.state_observer = Observer()
        self.state_observer.schedule(
            self.state_event_handler, str(self.path), recursive=True
        )
        self.state_observer.start()

    def stop_file_watcher(self):
        if self.state_observer:
            self.state_observer.stop()
            self.state_observer.join()

    def pause_file_watcher(self):
        if self.state_event_handler:
            self.state_event_handler.paused = True

    def resume_file_watcher(self):
        if self.state_event_handler:
            self.state_event_handler.paused = False

    def run_command(self, *args: str) -> str:
        return subprocess.run(
            args, capture_output=True, text=True, cwd=self.path
        ).stdout.strip()

    def init(self):
        self.path.mkdir(exist_ok=True, parents=True)

        if not (self.path / ".git").exists():
            logger.info(f"Initializing git repository at {self.path}")
            self.run_command("git", "init", "-b", "master")

        running_in_playwright = os.environ.get("RUNNING_IN_PLAYWRIGHT") == "true"
        if running_in_playwright or not self.run_command(
            "git", "config", "--get", "user.name"
        ):
            logger.info("Setting local git user name and email to Thymis Controller")
            self.run_command("git", "config", "user.name", "Thymis Controller")
            self.run_command(
                "git", "config", "user.email", "controller@noreply.thymis.io"
            )

    def add(self, *files: pathlib.Path):
        self.run_command("git", "add", "--intent-to-add", *files)
        unstaged_files = self.run_command("git", "diff", "--name-only").splitlines()
        logger.info(f"Adding changed files to git index: {', '.join(unstaged_files)}")
        self.run_command("git", "add", *files)

    def commit(self, message: str):
        logger.info(f"Committing changes to git: {message}")
        self.run_command("git", "commit", "-m", message)

    def head_commit(self) -> str:
        return self.run_command("git", "rev-parse", "HEAD")

    def history(self) -> Commit:
        try:
            result = self.run_command(
                "git",
                "rev-list",
                "HEAD",
                "--format=%H%x00%h%x00%s%x00%ci%x00%an",
                "--no-commit-header",
            )
        except subprocess.CalledProcessError:
            logger.exception("Error getting git history")
            return []

        return [
            Commit(
                SHA=sha,
                SHA1=sha1,
                message=message,
                date=datetime.datetime.fromisoformat(date),
                author=author,
            )
            for line in result.splitlines()
            for sha, sha1, message, date, author in [line.split("\x00")]
        ]

    def diff(self, refA: str, refB: str) -> str:
        refA = refA or "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
        refB = refB or "HEAD"

        return self.run_command("git", "diff", refA, refB, "state.json")

    def status(self) -> RepoStatus:
        try:
            result = self.run_command("git", "status", "--porcelain")
        except subprocess.CalledProcessError:
            logger.exception("Error getting git status")
            return RepoStatus(changes=[])

        return RepoStatus(
            changes=reversed(
                [
                    FileChange(
                        path=path,
                        dir=os.path.dirname(path),
                        file=os.path.basename(path),
                        diff=self.run_command("git", "diff", "HEAD", path),
                    )
                    for line in result.splitlines()
                    for path in line.split(maxsplit=1)[1:]
                ]
            )
        )

    def is_dirty(self) -> bool:
        return bool(self.run_command("git", "status", "--porcelain"))

    def has_root_commit(self) -> bool:
        result = self.run_command("git", "rev-list", "--max-parents=0", "HEAD")
        return bool(result)
