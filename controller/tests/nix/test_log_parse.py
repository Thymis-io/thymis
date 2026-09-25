"""Progress counters must count items (paths/builds), not bytes.

`nix copy` reports per-path byte offsets through the same PROGRESS result
fields as the whole-operation item counters, so a naive sum over every
activity type makes the displayed totals scale with payload size.
"""

import json

from thymis_controller.nix.log_parse import NixParser

COPY_PATH = 100
COPY_PATHS = 103
RESULT_PROGRESS = 105
RESULT_SET_EXPECTED = 106


def _nix(payload: dict) -> str:
    return "@nix " + json.dumps(payload) + "\n"


def _start(activity_id: int, type_: int, text: str = "") -> str:
    return _nix(
        {
            "action": "start",
            "id": activity_id,
            "level": 2,
            "type": type_,
            "text": text,
            "parent": 0,
        }
    )


def _stop(activity_id: int) -> str:
    return _nix({"action": "stop", "id": activity_id})


def _progress(activity_id: int, done: int, expected: int, running: int) -> str:
    return _nix(
        {
            "action": "result",
            "id": activity_id,
            "type": RESULT_PROGRESS,
            "fields": [done, expected, running, 0],
        }
    )


def _parse(lines: list[str]):
    parser = NixParser()
    parser.process_buffer(bytearray("".join(lines).encode()))
    return parser.get_model()


def test_copy_counters_ignore_byte_level_path_progress():
    # A 7-path copy, as emitted by `nix copy --log-format internal-json`:
    # the COPY_PATHS activity carries path counts, while the individual
    # COPY_PATH activity reports file byte offsets.
    lines = [
        _start(1, COPY_PATHS, "copying 7 paths"),
        _nix(
            {
                "action": "result",
                "id": 1,
                "type": RESULT_SET_EXPECTED,
                "fields": [COPY_PATH, 51833560],
            }
        ),
        _progress(1, 0, 7, 3),
        _start(2, COPY_PATH),
        _progress(2, 2078944, 2078944, 0),
        _stop(2),
        _progress(1, 7, 7, 0),
        _stop(1),
    ]

    model = _parse(lines)

    assert (model.done, model.expected) == (7, 7)
    assert model.failed == 0
