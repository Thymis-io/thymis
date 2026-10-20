import os
import pathlib

from thymis_agent import logger


def find_file(paths, filename):
    for path in paths:
        file_path = path / filename
        if os.path.exists(file_path):
            return file_path
    return None


def find_file_multiple_names(paths, filenames):
    for path in paths:
        for filename in filenames:
            file_path = path / filename
            if os.path.exists(file_path):
                return file_path
    return None


def atomic_write(path, data: str, mode: int = 0o600):
    """Durably replace `path` with `data`, forcing its permissions to `mode`.

    rename(2) atomically replaces the destination, so the readable path never
    points at a partial file. fsync of the data before and of the directory
    after means a crash leaves either the old or the new contents, never a
    truncated one.
    """
    path = pathlib.Path(path)
    tmp_path = path.with_name(f"{path.name}.new")
    # create restrictively, then apply `mode`: the content is never readable
    # by anyone else, not even for the instant between create and chmod
    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        f = os.fdopen(fd, "w", encoding="utf-8")
    except Exception:
        os.close(fd)
        raise
    with f:
        try:
            # O_CREAT's mode is masked by umask and ignored when tmp_path
            # survived an earlier crash, so set it explicitly
            os.fchmod(f.fileno(), mode)
        except OSError as e:
            # /boot and /boot/firmware are usually vfat, which has no per-file
            # permission bits; the mount's fmask governs instead
            logger.warning("Could not set mode %o on %s: %s", mode, tmp_path, e)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, path)
    dir_fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
