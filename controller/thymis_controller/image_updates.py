import base64
import ctypes
import fcntl
import logging
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
import time

from thymis_controller.config import global_settings

logger = logging.getLogger(__name__)

_KEY_UID = "Thymis Image Updates <image-updates@thymis.io>"
_CONFIGURATION_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*")


def config_uses_image_updates(modules) -> bool:
    """Return whether a resolved config selects the immutable A/B image format."""
    for module, settings in modules:
        if module.type == "thymis_controller.modules.thymis.ThymisDevice":
            image_format = settings.settings.get(
                "image_format", module.image_format.default
            )
            return image_format == "ab-repart-image"
    return False


def next_update_version(current_version: str, timestamp_ms: int | None = None) -> str:
    """Return a compact version newer than normal revision-based image versions."""
    candidate = (
        timestamp_ms if timestamp_ms is not None else time.time_ns() // 1_000_000
    )
    if current_version.isdecimal():
        candidate = max(candidate, int(current_version) + 1)
    return str(candidate)


_KEYRING_DIRNAME = "image-update-signing-keyring"


def _gpg_env(project_path: pathlib.Path) -> dict[str, str]:
    keyring = project_path / _KEYRING_DIRNAME
    keyring.mkdir(mode=0o700, parents=True, exist_ok=True)
    keyring.chmod(0o700)
    return {**os.environ, "GNUPGHOME": str(keyring)}


def _run_gpg(
    project_path: pathlib.Path, *args: str
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["gpg", "--batch", "--no-tty", *args],
        check=True,
        capture_output=True,
        env=_gpg_env(project_path),
    )


def ensure_update_signing_key(
    project_path: pathlib.Path | None = None,
) -> bytes:
    """Return the controller's binary OpenPGP update-verification key."""
    project_path = project_path or global_settings.PROJECT_PATH
    _gpg_env(project_path)
    with (project_path / ".image-update-signing-key.lock").open("w") as key_lock:
        fcntl.flock(key_lock, fcntl.LOCK_EX)
        listed = _run_gpg(project_path, "--with-colons", "--list-secret-keys")
        if b"sec:" not in listed.stdout:
            logger.info("Generating controller image-update signing key")
            _run_gpg(
                project_path,
                "--pinentry-mode",
                "loopback",
                "--passphrase",
                "",
                "--quick-generate-key",
                _KEY_UID,
                "ed25519",
                "sign",
                "0",
            )
        return _run_gpg(project_path, "--export", _KEY_UID).stdout


def update_public_key_base64(project_path: pathlib.Path | None = None) -> str:
    return base64.b64encode(ensure_update_signing_key(project_path)).decode("ascii")


def _exchange_directories(first: pathlib.Path, second: pathlib.Path) -> None:
    """Atomically swap two directories without making either name unavailable."""
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = libc.renameat2
    except AttributeError as error:
        raise OSError("renameat2 is required for atomic update publication") from error
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    if (
        renameat2(
            -100,
            os.fsencode(first),
            -100,
            os.fsencode(second),
            2,
        )
        != 0
    ):
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))


def _fsync_directory(path: pathlib.Path) -> None:
    directory_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def publish_update_package(
    package_path: pathlib.Path,
    configuration_id: str,
    project_path: pathlib.Path | None = None,
) -> pathlib.Path:
    """Atomically publish and sign a systemd-sysupdate package directory."""
    if _CONFIGURATION_ID.fullmatch(configuration_id) is None:
        raise ValueError(f"Unsafe configuration ID: {configuration_id!r}")
    project_path = project_path or global_settings.PROJECT_PATH
    package_path = package_path.resolve(strict=True)
    if not package_path.is_dir():
        raise ValueError(f"Update package is not a directory: {package_path}")

    updates_root = project_path / "image-updates"
    updates_root.mkdir(mode=0o755, parents=True, exist_ok=True)
    destination = updates_root / configuration_id
    ensure_update_signing_key(project_path)

    with tempfile.TemporaryDirectory(dir=updates_root) as temporary_directory:
        staging = pathlib.Path(temporary_directory) / configuration_id
        shutil.copytree(package_path, staging)
        manifest = staging / "SHA256SUMS"
        if not manifest.is_file():
            raise ValueError(f"Update package has no SHA256SUMS: {package_path}")
        _run_gpg(
            project_path,
            "--yes",
            "--pinentry-mode",
            "loopback",
            "--passphrase",
            "",
            "--detach-sign",
            "--output",
            str(staging / "SHA256SUMS.gpg"),
            str(manifest),
        )

        with (updates_root / f".{configuration_id}.lock").open("w") as publish_lock:
            fcntl.flock(publish_lock, fcntl.LOCK_EX)
            if destination.exists():
                _exchange_directories(staging, destination)
                _fsync_directory(updates_root)
                shutil.rmtree(staging)
            else:
                staging.rename(destination)
                _fsync_directory(updates_root)

    return destination
