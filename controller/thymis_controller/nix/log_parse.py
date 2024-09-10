import asyncio
import dataclasses
import json
import logging
from enum import IntEnum
from typing import Annotated, Any, List, Literal, Optional, Union

import jinja2
from pydantic import BaseModel, Discriminator, Tag, ValidationError
from thymis_controller.nix import NIX_CMD

logger = logging.getLogger(__name__)


class ActivityType(IntEnum):
    UNKNOWN = 0
    COPY_PATH = 100
    FILE_TRANSFER = 101
    REALISE = 102
    COPY_PATHS = 103
    BUILDS = 104
    BUILD = 105
    OPTIMISE_STORE = 106
    VERIFY_PATHS = 107
    SUBSTITUTE = 108
    QUERY_PATH_INFO = 109
    POST_BUILD_HOOK = 110
    BUILD_WAITING = 111
    FETCH_TREE = 112


class ResultType(IntEnum):
    FILE_LINKED = 100
    BUILD_LOG_LINE = 101
    UNTRUSTED_PATH = 102
    CORRUPTED_PATH = 103
    SET_PHASE = 104
    PROGRESS = 105
    SET_EXPECTED = 106
    POST_BUILD_LOG_LINE = 107
    FETCH_STATUS = 108


def get_nix_line_discriminator(v: Any):
    if isinstance(v, dict):
        if "action" in v:
            if v["action"] == "msg":
                # discriminate between MessageNixLine and ErrorInfoNixLine
                # using "raw_msg"
                if "raw_msg" in v:
                    return "msg_ei"
                return "msg"
            # action is "start", "stop", or "result"
            return v["action"]
    action = getattr(v, "action", None)
    if action == "msg":
        if hasattr(v, "raw_msg"):
            return "msg_ei"
        return "msg"
    return action


class MessageNixLine(BaseModel):
    action: Literal["msg"]
    level: int
    msg: str


class TraceNixLine(BaseModel):
    raw_msg: str


class ErrorInfoNixLine(BaseModel):
    action: Literal["msg"]
    level: int
    msg: str
    raw_msg: str
    line: Optional[int] = None
    column: Optional[int] = None
    file: Optional[str] = None
    trace: Optional[List[TraceNixLine]] = None


class StartActivityNixLine(BaseModel):
    action: Literal["start"]
    id: int
    level: int
    type: int
    text: str
    parent: int
    fields: Optional[List[Union[int, str]]] = None


class StopActivityNixLine(BaseModel):
    action: Literal["stop"]
    id: int


class ResultNixLine(BaseModel):
    action: Literal["result"]
    id: int
    type: int
    fields: Optional[List[Union[int, str]]] = None


class ParsedNixLineModel(BaseModel):
    nix_line: Annotated[
        Union[
            Annotated[MessageNixLine, Tag("msg")],
            Annotated[ErrorInfoNixLine, Tag("msg_ei")],
            Annotated[StartActivityNixLine, Tag("start")],
            Annotated[StopActivityNixLine, Tag("stop")],
            Annotated[ResultNixLine, Tag("result")],
        ],
        Discriminator(get_nix_line_discriminator),
    ]


def parse_nix_line(line: bytes) -> ParsedNixLineModel:
    line = line[len(b"@nix ") :]
    parsed = json.loads(line)
    parsed_obj = ParsedNixLineModel.model_validate({"nix_line": parsed})
    return parsed_obj


async def log_exceptions(awaitable):
    try:
        return await awaitable
    except Exception:
        import sys

        exc_info = sys.exc_info()
        logger.exception("Unhandled exception", exc_info=exc_info)


@dataclasses.dataclass
class NixActivityResult:
    type: int
    fields: List[Union[int, str]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class ActivitiesDoneExpectedFailed:
    # def __init__(self):
    #     self.activity_info_by_id = {}
    #     self.done = 0
    #     self.expected = 0
    #     self.failed = 0
    activity_info_by_id: dict[int, "ActivityInfo"] = dataclasses.field(
        default_factory=dict
    )
    done: int = 0
    expected: int = 0
    failed: int = 0


@dataclasses.dataclass
class ActivityInfo:
    type: int
    done: int = 0
    expected: int = 0
    running: int = 0
    failed: int = 0
    phase: Optional[str] = None
    expected_by_type: dict[int, int] = dataclasses.field(default_factory=dict)


class NixProcess:
    def __init__(self, args, cwd=None, env=None):
        self.args = args + ["--log-format", "internal-json", "-v"]
        self.cwd = cwd
        self.env = env

        self.stdout = bytearray()
        self.stderr = bytearray()

        self.subscribers = set()

        self.process = None

        self.activity_info_by_id: dict[int, ActivityInfo] = {}
        self.activities_done_expect_failed_by_type: dict[
            int, ActivitiesDoneExpectedFailed
        ] = {}
        self.error_logs = []  # level 0
        self.warnings = []  # level 1
        self.notices = []  # level 2
        self.infos = []  # level 3
        self.other_messages = []  # level 4 and above

        self.errors = []

        self.filesLinked = 0
        self.bytesLinked = 0
        self.corruptedPaths = 0
        self.untrustedPaths = 0

    async def stream_reader(
        self,
        stream: asyncio.StreamReader | None,
        out: bytearray,
        parse_lines: bool = False,
    ):
        while True:
            line = await stream.readline()
            if not line:
                # readline doc:
                # On success, return chunk that ends with newline.
                # If only partial line can be read due to EOF,
                # return incomplete line without terminating newline.
                # When EOF was reached while no bytes read, empty bytes object is returned.
                #
                # So, if line is empty, we have reached EOF
                break
            out.extend(line)
            if parse_lines:
                self.handle_line(line)
            await self.notify_subscribers()

    async def run(self):
        proc = await asyncio.create_subprocess_exec(
            NIX_CMD[0],
            *NIX_CMD[1:],
            *self.args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self.env,
        )
        self.process = proc
        await self.notify_subscribers()
        logger.info("Started process %s", proc.pid)

        read_stdout_task = asyncio.create_task(
            log_exceptions(self.stream_reader(proc.stdout, self.stdout))
        )
        read_stderr_task = asyncio.create_task(
            log_exceptions(
                self.stream_reader(proc.stderr, self.stderr, parse_lines=True)
            )
        )

        r = await proc.wait()
        if r != 0:
            raise RuntimeError(
                f"Command {NIX_CMD[0]} {' '.join(self.args)} failed with exit code {r}"
            )

        await asyncio.gather(read_stdout_task, read_stderr_task)

        return r

    async def notify_subscribers(self):
        for subscriber in self.subscribers:
            await subscriber(self)

    def subscribe(self, subscriber):
        self.subscribers.add(subscriber)

    def handle_line(self, line):
        # expect: line is "@nix {jsonjson}"
        if not line.startswith(b"@nix "):
            raise ValueError(f"Unexpected line: {line}")
        parsed = parse_nix_line(line)
        # logger.info("Parsed lineA: %s", parsed)

        if isinstance(parsed.nix_line, StartActivityNixLine):
            self.activity_info_by_id[parsed.nix_line.id] = ActivityInfo(
                parsed.nix_line.type
            )
            self.activities_done_expect_failed_by_type.setdefault(
                parsed.nix_line.type, ActivitiesDoneExpectedFailed()
            )
            self.activities_done_expect_failed_by_type[
                parsed.nix_line.type
            ].activity_info_by_id[parsed.nix_line.id] = self.activity_info_by_id[
                parsed.nix_line.id
            ]
        elif isinstance(parsed.nix_line, StopActivityNixLine):
            activity_info = self.activity_info_by_id[parsed.nix_line.id]
            activity_by_type = self.activities_done_expect_failed_by_type[
                activity_info.type
            ]
            activity_by_type.done += activity_info.done
            activity_by_type.failed += activity_info.failed

            for type_, count in activity_info.expected_by_type.items():
                self.activities_done_expect_failed_by_type[type_].expected -= count

            del activity_by_type.activity_info_by_id[parsed.nix_line.id]
            del self.activity_info_by_id[parsed.nix_line.id]
        elif isinstance(parsed.nix_line, ResultNixLine):
            line_type = parsed.nix_line.type
            if line_type == ResultType.FILE_LINKED:
                self.filesLinked += 1
                self.bytesLinked += int(parsed.nix_line.fields[0])
            elif line_type == ResultType.UNTRUSTED_PATH:
                self.untrustedPaths += 1
            elif line_type == ResultType.CORRUPTED_PATH:
                self.corruptedPaths += 1
            elif line_type == ResultType.SET_PHASE:
                activity_info = self.activity_info_by_id[parsed.nix_line.id]
                activity_info.phase = parsed.nix_line.fields[0]
            elif line_type == ResultType.PROGRESS:
                activity_info = self.activity_info_by_id[parsed.nix_line.id]
                activity_info.done = parsed.nix_line.fields[0]
                activity_info.expected = parsed.nix_line.fields[1]
                activity_info.running = parsed.nix_line.fields[2]
                activity_info.failed = parsed.nix_line.fields[3]
            elif line_type == ResultType.SET_EXPECTED:
                activity_info = self.activity_info_by_id[parsed.nix_line.id]
                set_for_type = parsed.nix_line.fields[0]
                self.activities_done_expect_failed_by_type.setdefault(
                    set_for_type, ActivitiesDoneExpectedFailed()
                )
                self.activities_done_expect_failed_by_type[
                    set_for_type
                ].expected -= activity_info.expected_by_type.get(set_for_type, 0)
                activity_info.expected_by_type[set_for_type] = int(
                    parsed.nix_line.fields[1]
                )
                self.activities_done_expect_failed_by_type[
                    set_for_type
                ].expected += activity_info.expected_by_type[set_for_type]
            else:
                logger.info("Unhandled result: %s", parsed)
        elif isinstance(parsed.nix_line, MessageNixLine):
            if parsed.nix_line.level == 0:
                self.error_logs.append(parsed.nix_line)
            elif parsed.nix_line.level == 1:
                self.warnings.append(parsed.nix_line)
            elif parsed.nix_line.level == 2:
                self.notices.append(parsed.nix_line)
            elif parsed.nix_line.level == 3:
                self.infos.append(parsed.nix_line)
            elif parsed.nix_line.level >= 4:
                self.other_messages.append(parsed.nix_line)
        elif isinstance(parsed.nix_line, ErrorInfoNixLine):
            self.errors.append(parsed.nix_line)
        else:
            logger.info("Unhandled line: %s", parsed)

        return parsed

    def calc_activities_done_expected_failed(self):
        global_done = 0
        global_running = 0
        global_expected = 0
        global_failed = 0
        for type_, activities in self.activities_done_expect_failed_by_type.items():
            done = activities.done
            excepted = activities.done
            running = 0
            failed = activities.failed
            for activity in activities.activity_info_by_id.values():
                done += activity.done
                excepted += activity.expected
                running += activity.running
                failed += activity.failed
            global_done += done
            global_running += running
            global_expected += excepted
            global_failed += failed
        return global_done, global_expected, global_running, global_failed

    def get_model(self):
        (
            global_done,
            global_expected,
            global_running,
            global_failed,
        ) = self.calc_activities_done_expected_failed()
        return {
            "global_done": global_done,
            "global_expected": global_expected,
            "global_running": global_running,
            "global_failed": global_failed,
            "errors": self.errors,
            "error_logs": self.error_logs,
            "warnings": self.warnings,
            "notices": self.notices,
            "infos": self.infos,
        }
