import json

from thymis_controller.nix.log_parse import ActivityType, NixParser


def nix_line(payload: dict) -> bytes:
    return f"@nix {json.dumps(payload)}\n".encode()


def test_transfer_progress_is_exposed_separately_from_process_progress():
    parser = NixParser()
    buffer = bytearray(
        b"".join(
            [
                nix_line(
                    {
                        "action": "start",
                        "id": 1,
                        "level": 3,
                        "type": ActivityType.COPY_PATH,
                        "text": "copying paths",
                        "parent": 0,
                    }
                ),
                nix_line(
                    {
                        "action": "result",
                        "id": 1,
                        "type": 105,
                        "fields": [2, 10, 1, 0],
                    }
                ),
                nix_line(
                    {
                        "action": "start",
                        "id": 2,
                        "level": 3,
                        "type": ActivityType.FILE_TRANSFER,
                        "text": "transferring",
                        "parent": 1,
                    }
                ),
                nix_line(
                    {
                        "action": "result",
                        "id": 2,
                        "type": 105,
                        "fields": [4096, 8192, 1, 0],
                    }
                ),
            ]
        )
    )

    assert parser.process_buffer(buffer)

    status = parser.get_model()
    assert status.transfer.done == 4096
    assert status.transfer.expected == 8192
    assert status.transfer.running == 1
    assert status.transfer.failed == 0
    assert status.done == 4098
    assert status.expected == 8202
