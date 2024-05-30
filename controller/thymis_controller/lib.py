import base64
import os


def read_into_base64(path: str):
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            extension = os.path.splitext(path)[1][1:]

            if extension == "svg":
                extension = "svg+xml"

            return f"data:image/{extension};base64,{encoded}"
    except FileNotFoundError:
        print(f"File not found: {path}")
        return None
