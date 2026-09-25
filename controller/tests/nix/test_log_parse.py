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


def test_multi_path_copy_keeps_one_denominator():
    """A 2-path copy declares 2000 bytes up front; the bar must not restart.

    The SET_EXPECTED of the COPY_PATHS batch is the only honest denominator:
    it stays 2000 from the first byte to the last, so the progress bar runs
    0-100% once instead of jumping back at every path boundary.
    """
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 2 paths")),
                nix_line(set_expected(1, ActivityType.COPY_PATH, 2000)),
                nix_line(
                    copy_path(
                        2,
                        "/nix/store/aaa-first",
                        "local://",
                        "ssh-ng://root@127.0.0.1",
                    )
                ),
                nix_line(progress(2, 1000, 1000)),
                # the first path finishes, the second one takes over
                nix_line(stop_activity(2)),
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
    # transfer bytes are exposed separately: the process totals stay on items
    assert status.done == 2
    assert status.expected == 10


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


def test_copy_counters_ignore_byte_level_path_progress():
    """Process counters count items (paths), never the bytes of a single path.

    `nix copy` reports per-path byte offsets through the same PROGRESS fields
    as the whole-operation item counters, so a naive sum over every activity
    type makes the displayed totals scale with payload size.
    """
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 7 paths")),
                nix_line(set_expected(1, ActivityType.COPY_PATH, 51833560)),
                nix_line(progress(1, 0, 7, running=3)),
                # one path of the batch, reporting file byte offsets
                nix_line(start_activity(2, ActivityType.COPY_PATH, "")),
                nix_line(progress(2, 2078944, 2078944)),
                nix_line(stop_activity(2)),
                nix_line(progress(1, 7, 7)),
                nix_line(stop_activity(1)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert (status.done, status.expected) == (7, 7)
    assert status.failed == 0
