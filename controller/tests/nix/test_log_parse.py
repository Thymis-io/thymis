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


def test_copy_to_target_device_reports_transferred_bytes():
    """`nix copy --to ssh-ng://...` reports byte progress on COPY_PATH activities."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                # batch declaring the total size it will copy
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 2 paths")),
                nix_line(set_expected(1, ActivityType.COPY_PATH, 2000)),
                # first path
                nix_line(
                    start_activity(
                        2,
                        ActivityType.COPY_PATH,
                        "copying path '/nix/store/aaa-first' to 'ssh-ng://root@127.0.0.1'",
                    )
                ),
                nix_line(progress(2, 500, 1000)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.done == 500
    assert status.transfer.expected == 2000
    assert status.transfer.running == 1
    assert status.transfer.failed == 0

    buffer = bytearray(
        b"".join(
            [
                nix_line(progress(2, 1000, 1000)),
                nix_line(stop_activity(2)),
                # second path
                nix_line(
                    start_activity(
                        3,
                        ActivityType.COPY_PATH,
                        "copying path '/nix/store/bbb-second' to 'ssh-ng://root@127.0.0.1'",
                    )
                ),
                nix_line(progress(3, 400, 1000)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.done == 1400
    assert status.transfer.expected == 2000
    assert status.transfer.running == 1

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
    assert status.transfer.done == 2000
    assert status.transfer.expected == 2000
    assert status.transfer.running == 0


def test_copy_path_wrapping_file_transfer_is_not_counted_twice():
    """nix nests the raw file download inside the copy path moving the same bytes."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 1 paths")),
                nix_line(set_expected(1, ActivityType.COPY_PATH, 1000)),
                nix_line(
                    start_activity(
                        2,
                        ActivityType.COPY_PATH,
                        "copying path '/nix/store/aaa-first' from 'https://cache.nixos.org'",
                    )
                ),
                nix_line(
                    start_activity(
                        3,
                        ActivityType.FILE_TRANSFER,
                        "downloading 'https://cache.nixos.org/nar/abc.nar.zst'",
                        parent=2,
                    )
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
    assert status.transfer.done == 1000
    assert status.transfer.expected == 1000


def test_bare_file_transfer_is_reported_when_no_path_is_copied():
    """HTTP fetches outside a store path copy still count as transferred bytes."""
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(start_activity(1, ActivityType.COPY_PATHS, "copying 3 paths")),
                nix_line(progress(1, 2, 10, running=1)),
                nix_line(
                    start_activity(
                        2,
                        ActivityType.FILE_TRANSFER,
                        "downloading 'https://cache.nixos.org/nix-cache-info'",
                    )
                ),
                nix_line(progress(2, 4096, 8192, running=1)),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.done == 4096
    assert status.transfer.expected == 8192
    assert status.transfer.running == 1
    assert status.transfer.failed == 0
    # transfer progress is exposed separately, the process totals are untouched
    assert status.done == 4098
    assert status.expected == 8202
