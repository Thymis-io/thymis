import subprocess


def check_calendar(value: str, iterations: int) -> list[str]:
    try:
        result = subprocess.run(
            [
                "systemd-analyze",
                "calendar",
                value,
                f"--iterations={iterations}",
            ],
            capture_output=True,
            check=True,
        )
        output = result.stdout.decode().strip()
        result = []
        for line in output.split("\n"):
            if "(in UTC)" in line:
                time = line.split(":", 1)[1].strip()
                result.append(time)
        if len(result) != iterations:
            raise ValueError("Could not parse all calendar outputs")
        return result
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Invalid calendar value: {value}") from e


def check_timespan(value: str) -> str:
    try:
        result = subprocess.run(
            [
                "systemd-analyze",
                "timespan",
                value,
            ],
            capture_output=True,
            check=True,
        )
        output = result.stdout.decode().strip()
        for line in output.split("\n"):
            if "Human" in line:
                time = line.split(":", 1)[1].strip()
                return time
        raise ValueError("Could not parse time-span output")
    except subprocess.CalledProcessError as e:
        raise ValueError(f"Invalid timespan value: {value}") from e
