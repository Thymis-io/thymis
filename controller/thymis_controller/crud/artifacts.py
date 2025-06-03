import subprocess
from pathlib import Path


def get_media_type(path: Path) -> str | None:
    try:
        return (
            subprocess.run(
                ["file", "--mime-type", "--brief", path],
                stdout=subprocess.PIPE,
                check=True,
            )
            .stdout.strip()
            .decode("utf-8")
        )
    except subprocess.CalledProcessError:
        return None
