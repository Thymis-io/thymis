import json

from thymis_controller.nix.log_parse import ActivityType, NixParser, ResultType


def nix_line(payload: dict) -> bytes:
    return f"@nix {json.dumps(payload)}\n".encode()


def start_activity(activity_id: int, type_: int, text: str, parent: int = 0) -> dict:
    return {
        "action": "start",
        "id": activity_id,
        "level": 3,
        "type": type_,
        "text": text,
        "parent": parent,
    }


def stop_activity(activity_id: int) -> dict:
    return {"action": "stop", "id": activity_id}


def set_expected(activity_id: int, type_: int, expected: int) -> dict:
    return {
        "action": "result",
        "id": activity_id,
        "type": ResultType.SET_EXPECTED,
        "fields": [type_, expected],
    }


def progress(activity_id: int, done: int, expected: int, running: int = 0) -> dict:
    return {
        "action": "result",
        "id": activity_id,
        "type": ResultType.PROGRESS,
        "fields": [done, expected, running, 0],
    }


def copy_path(activity_id: int, path: str, from_store: str, to_store: str) -> dict:
    """A COPY_PATH activity as nix emits it: fields are [path, from, to]."""
    start = start_activity(
        activity_id,
        ActivityType.COPY_PATH,
        f"copying path '{path}' from '{from_store}' to '{to_store}'",
    )
    start["fields"] = [path, from_store, to_store]
    return start


def file_transfer(activity_id: int, url: str, parent: int = 0) -> dict:
    return start_activity(
        activity_id,
        ActivityType.FILE_TRANSFER,
        f"downloading '{url}'",
        parent=parent,
    )


def test_copy_to_target_device_is_reported_as_upload():
    """`nix copy --to ssh-ng://...` moves bytes out of the local store."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                # batch declaring the total size it will copy
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 2 paths")),
                nix_line(set_expected(1, ActivityType.COPY_PATH, 2000)),
                # first path
                nix_line(
                    copy_path(
                        2,
                        "/nix/store/aaa-first",
                        "local://",
                        "ssh-ng://root@127.0.0.1",
                    )
                ),
                nix_line(progress(2, 500, 1000)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.upload.done == 500
    assert status.transfer.upload.expected == 2000
    assert status.transfer.upload.running == 1
    assert status.transfer.upload.failed == 0
    assert status.transfer.download is None

    buffer = bytearray(
        b"".join(
            [
                nix_line(progress(2, 1000, 1000)),
                nix_line(stop_activity(2)),
                # second path
                nix_line(
                    copy_path(
                        3,
                        "/nix/store/bbb-second",
                        "local://",
                        "ssh-ng://root@127.0.0.1",
                    )
                ),
                nix_line(progress(3, 400, 1000)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.upload.done == 1400
    assert status.transfer.upload.expected == 2000
    assert status.transfer.upload.running == 1

    buffer = bytearray(
        b"".join(
            [
                nix_line(progress(3, 1000, 1000)),
                nix_line(stop_activity(3)),
                nix_line(stop_activity(1)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.upload.done == 2000
    assert status.transfer.upload.expected == 2000
    assert status.transfer.upload.running == 0


def test_download_from_cache_is_not_counted_twice():
    """nix nests the raw file download inside the copy path moving the same bytes."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 1 paths")),
                nix_line(set_expected(1, ActivityType.COPY_PATH, 1000)),
                nix_line(
                    copy_path(
                        2,
                        "/nix/store/aaa-first",
                        "https://cache.nixos.org",
                        "local://",
                    )
                ),
                nix_line(
                    file_transfer(3, "https://cache.nixos.org/nar/abc.nar.zst", 2)
                ),
                nix_line(progress(2, 1000, 1000)),
                nix_line(progress(3, 600, 600)),
                nix_line(stop_activity(3)),
                nix_line(stop_activity(2)),
                nix_line(stop_activity(1)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.download.done == 1000
    assert status.transfer.download.expected == 1000
    assert status.transfer.download.running == 0
    assert status.transfer.upload is None


def test_bare_file_transfer_is_reported_as_download():
    """HTTP fetches outside a store path copy still count as downloaded bytes."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 3 paths")),
                nix_line(progress(1, 2, 10, running=1)),
                nix_line(
                    file_transfer(2, "https://cache.nixos.org/nix-cache-info"),
                ),
                nix_line(progress(2, 4096, 8192, running=1)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.download.done == 4096
    assert status.transfer.download.expected == 8192
    assert status.transfer.download.running == 1
    assert status.transfer.download.failed == 0
    # transfer progress is exposed separately, the process totals are untouched
    assert status.done == 4098
    assert status.expected == 8202


def test_download_and_upload_are_reported_side_by_side():
    """A process can both pull a path from a cache and push one to a device."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(
                    copy_path(
                        1,
                        "/nix/store/aaa-cached",
                        "https://cache.nixos.org",
                        "local://",
                    )
                ),
                nix_line(progress(1, 250, 500)),
                nix_line(
                    copy_path(
                        2,
                        "/nix/store/bbb-built",
                        "local://",
                        "ssh-ng://root@127.0.0.1",
                    )
                ),
                nix_line(progress(2, 100, 400)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.download.done == 250
    assert status.transfer.download.expected == 500
    assert status.transfer.upload.done == 100
    assert status.transfer.upload.expected == 400
    assert status.transfer.other is None
