# Package inputs only: keeps `build/`, `*.egg-info`, `.venv` out of path-based
# builds, where setuptools would reuse a stale `build/`.
{ lib }:
lib.fileset.unions [
  ./pyproject.toml
  ./uv.lock
  ./README.md
  (lib.fileset.fileFilter (file: !(file.hasExt "pyc")) ./thymis_agent)
]
