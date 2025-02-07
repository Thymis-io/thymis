import datetime
import logging
import pathlib
import subprocess

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Commit(BaseModel):
    SHA: str
    SHA1: str
    message: str
    date: datetime.datetime
    author: str


class Repo:
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.init()

    def run_command(self, *args: str) -> str:
        return subprocess.run(
            args, capture_output=True, text=True, cwd=self.path
        ).stdout.strip()

    def init(self):
        self.path.mkdir(exist_ok=True, parents=True)

        if not (self.path / ".git").exists():
            logger.info(f"Initializing git repository at {self.path}")
            self.run_command("git", "init", "-b", "master")

        if not self.run_command("git", "config", "--get", "user.name"):
            logger.info("Setting local git user name and email to Thymis Controller")
            self.run_command("git", "config", "user.name", "Thymis Controller")
            self.run_command(
                "git", "config", "user.email", "controller@noreply.thymis.io"
            )

    def add(self, *files: pathlib.Path):
        logger.info(f"Adding files to git: {', '.join(files)}")
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
