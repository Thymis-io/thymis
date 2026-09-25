"""Authenticated streaming endpoint and conversation store for the assistant."""

from __future__ import annotations

import datetime
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from thymis_controller.agent_runtime import (
    ChatMessage,
    ChatRequest,
    chat_message_from_ui_message,
    history_from_transcript,
    image_file_part_from_ui_message,
    resolve_model,
    stream_chat,
)
from thymis_controller.agent_tools import ThymisTools
from thymis_controller.config import global_settings
from thymis_controller.crud import agent_conversation
from thymis_controller.db_models import AgentConversation
from thymis_controller.dependencies import DBSessionAD, EngineAD, UserIdentityAD
from thymis_controller.models.agent import (
    AgentConversationDetail,
    AgentConversationRename,
    AgentConversationSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


def _sse_event(payload: dict[str, object]) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n\n".encode(
        "utf-8"
    )


def _sse_done() -> bytes:
    return b"data: [DONE]\n\n"


def _require_identity(user_identity: str | None) -> str:
    if user_identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No valid session"
        )
    return user_identity


def _conversation_or_404(
    db_session: Session, user_identity: str, conversation_id: uuid.UUID
) -> AgentConversation:
    conversation = agent_conversation.get(db_session, user_identity, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


def _summary(
    db_session: Session, conversation: AgentConversation
) -> AgentConversationSummary:
    return AgentConversationSummary(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=agent_conversation.message_count(db_session, conversation),
    )


def _detail(
    db_session: Session, conversation: AgentConversation
) -> AgentConversationDetail:
    return AgentConversationDetail(
        **_summary(db_session, conversation).model_dump(),
        messages=agent_conversation.transcript(conversation),
    )


@router.get("/agent/conversations", response_model=list[AgentConversationSummary])
def list_conversations(
    db_session: DBSessionAD,
    user_identity: UserIdentityAD,
    q: Annotated[str | None, Query(max_length=120)] = None,
) -> list[AgentConversationSummary]:
    """List the signed-in operator's saved assistant conversations."""

    identity = _require_identity(user_identity)
    return [
        _summary(db_session, conversation)
        for conversation in agent_conversation.list_for_user(db_session, identity, q)
    ]


@router.post(
    "/agent/conversations",
    response_model=AgentConversationDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    db_session: DBSessionAD, user_identity: UserIdentityAD
) -> AgentConversationDetail:
    """Start a new empty assistant conversation."""

    identity = _require_identity(user_identity)
    conversation = agent_conversation.create(db_session, identity)
    return _detail(db_session, conversation)


@router.get(
    "/agent/conversations/{conversation_id}", response_model=AgentConversationDetail
)
def get_conversation(
    conversation_id: uuid.UUID, db_session: DBSessionAD, user_identity: UserIdentityAD
) -> AgentConversationDetail:
    """Return one saved conversation with its full transcript."""

    identity = _require_identity(user_identity)
    conversation = _conversation_or_404(db_session, identity, conversation_id)
    return _detail(db_session, conversation)


@router.patch(
    "/agent/conversations/{conversation_id}", response_model=AgentConversationDetail
)
def rename_conversation(
    conversation_id: uuid.UUID,
    rename: AgentConversationRename,
    db_session: DBSessionAD,
    user_identity: UserIdentityAD,
) -> AgentConversationDetail:
    """Give one saved conversation a title of the operator's choosing."""

    identity = _require_identity(user_identity)
    conversation = _conversation_or_404(db_session, identity, conversation_id)
    agent_conversation.rename(db_session, conversation, rename.title)
    return _detail(db_session, conversation)


@router.delete(
    "/agent/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: uuid.UUID, db_session: DBSessionAD, user_identity: UserIdentityAD
) -> Response:
    """Delete one saved conversation."""

    identity = _require_identity(user_identity)
    conversation = _conversation_or_404(db_session, identity, conversation_id)
    agent_conversation.delete(db_session, conversation)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/agent/files/{file_id}")
def get_file(
    file_id: uuid.UUID, db_session: DBSessionAD, user_identity: UserIdentityAD
) -> Response:
    """Serve one conversation attachment to the operator who owns it."""

    identity = _require_identity(user_identity)
    agent_file = agent_conversation.get_file(db_session, identity, file_id)
    if agent_file is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File not found"
        )
    return Response(
        content=agent_file.content,
        media_type=agent_file.media_type,
        # Attachments are scoped to one operator, so they must never be served
        # from a shared cache after a different operator signs in.
        headers={"Cache-Control": "private, no-store"},
    )


DEFAULT_ATTACHMENT_FILENAME = "vnc-screenshot.png"
FILE_URL_PREFIX = "/api/agent/files/"


def _utc_timestamp(moment: datetime.datetime | None = None) -> str:
    """RFC 3339 UTC timestamp, which is what the browser parses as UTC."""
    instant = moment or datetime.datetime.now(datetime.timezone.utc)
    return instant.astimezone(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _attachment_filename(file_part: dict[str, Any] | None) -> str:
    """Take a stored filename from the browser's upload, minus any path."""
    filename = (file_part or {}).get("filename")
    if isinstance(filename, str) and filename.strip():
        return filename.strip().rsplit("/", 1)[-1].rsplit("\\", 1)[-1][:255]
    return DEFAULT_ATTACHMENT_FILENAME


def _file_id_from_url(url: Any) -> uuid.UUID | None:
    """Read a stored attachment id back out of the URL we handed to the browser."""
    if not isinstance(url, str) or not url.startswith(FILE_URL_PREFIX):
        return None
    try:
        return uuid.UUID(url.removeprefix(FILE_URL_PREFIX))
    except ValueError:
        return None


def _stored_screenshot(
    db_session: Session, user_identity: str, message: Any
) -> bytes | None:
    """Load the screenshot a stored user message attached, so a retry keeps it."""
    if not isinstance(message, dict):
        return None
    for part in message.get("parts") or []:
        file_id = _file_id_from_url(
            (part or {}).get("url") if isinstance(part, dict) else None
        )
        if file_id is None:
            continue
        agent_file = agent_conversation.get_file(db_session, user_identity, file_id)
        if agent_file is not None:
            return agent_file.content
    return None


def _user_ui_message(
    message_id: str,
    content: str,
    created_at: str,
    attachment_url: str | None = None,
    attachment_filename: str = DEFAULT_ATTACHMENT_FILENAME,
) -> dict[str, Any]:
    """Serialize one user prompt as an AI SDK UI message.

    An attached VNC screenshot is referenced by URL rather than embedded, so the
    stored transcript stays small and the image still renders after a reload.
    """
    parts: list[dict[str, Any]] = [{"type": "text", "text": content}]
    if attachment_url is not None:
        parts.append(
            {
                "type": "file",
                "mediaType": "image/png",
                "filename": attachment_filename,
                "url": attachment_url,
            }
        )
    return {
        "id": message_id,
        "role": "user",
        "parts": parts,
        "metadata": {"createdAt": created_at},
    }


def _assistant_ui_message(
    message_id: str, parts: list[dict[str, Any]], created_at: str
) -> dict[str, Any]:
    return {
        "id": message_id,
        "role": "assistant",
        "parts": parts,
        "metadata": {"createdAt": created_at},
    }


def _prepare_submitted_turn(
    db_session: Session,
    conversation: AgentConversation,
    prompt: ChatMessage,
    file_part: dict[str, Any] | None,
    turn_started: datetime.datetime,
) -> list[Any]:
    """Store the new user prompt and return the history that precedes it."""
    history = agent_conversation.transcript(conversation)
    if not history:
        agent_conversation.rename(
            db_session,
            conversation,
            agent_conversation.title_from_prompt(prompt.content),
        )
    attachment_url = None
    if prompt.screenshot is not None:
        stored_file = agent_conversation.create_file(
            db_session,
            conversation,
            content=prompt.screenshot,
            media_type="image/png",
            filename=_attachment_filename(file_part),
        )
        attachment_url = f"{FILE_URL_PREFIX}{stored_file.id}"
    agent_conversation.append_messages(
        db_session,
        conversation,
        [
            _user_ui_message(
                str(uuid.uuid4()),
                prompt.content,
                _utc_timestamp(turn_started),
                attachment_url,
                _attachment_filename(file_part),
            )
        ],
        now=turn_started.replace(tzinfo=None),
    )
    return history


def _prepare_regenerated_turn(
    db_session: Session,
    user_identity: str,
    conversation: AgentConversation,
) -> tuple[ChatMessage, list[Any]]:
    """Re-run the stored trailing prompt, after dropping the reply to replace."""
    stored = agent_conversation.transcript(conversation)
    if stored and stored[-1].get("role") == "assistant":
        agent_conversation.delete_last_message(db_session, conversation)
        stored = stored[:-1]
    prompt = chat_message_from_ui_message(stored[-1]) if stored else None
    if prompt is None or prompt.role != "user":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This conversation has no turn to regenerate",
        )
    # Re-attach a stored screenshot so the retried turn asks the same question.
    screenshot = _stored_screenshot(db_session, user_identity, stored[-1])
    if screenshot is not None:
        prompt = ChatMessage(role="user", content=prompt.content, screenshot=screenshot)
    return prompt, stored[:-1]


class _TranscriptBuilder:
    """Accumulate the AI SDK UI parts of one streamed assistant turn."""

    def __init__(self) -> None:
        self.parts: list[dict[str, Any]] = []
        self._text: dict[str, Any] | None = None
        self._tools: dict[str, dict[str, Any]] = {}

    def start_text(self) -> None:
        self._text = {"type": "text", "text": ""}
        self.parts.append(self._text)

    def add_text(self, delta: str) -> None:
        assert self._text is not None
        self._text["text"] += delta

    def end_text(self) -> None:
        self._text = None

    def add_tool_call(self, tool_call_id: str, tool_name: str, tool_input: Any) -> None:
        part = {
            "type": "dynamic-tool",
            "toolCallId": tool_call_id,
            "toolName": tool_name,
            "state": "input-available",
            "input": tool_input,
        }
        self.parts.append(part)
        self._tools[tool_call_id] = part

    def add_tool_result(self, tool_call_id: str, output: Any) -> None:
        part = self._tools.get(tool_call_id)
        if part is not None:
            part["state"] = "output-available"
            part["output"] = output

    def add_entity_link(self, entity: Any) -> None:
        self.parts.append({"type": "data-entity-link", "data": entity})


@router.post("/agent/chat")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    engine: EngineAD,
    user_identity: UserIdentityAD,
) -> StreamingResponse:
    """Stream one assistant turn for the current signed-in operator."""

    if not global_settings.AGENT_MODEL:
        raise HTTPException(
            status_code=503,
            detail="Assistant is not configured. Set THYMIS_AGENT_MODEL and its provider credentials.",
        )
    try:
        model = resolve_model(
            global_settings.AGENT_MODEL,
            base_url=global_settings.AGENT_BASE_URL,
            api_key=global_settings.AGENT_API_KEY,
        )
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    identity = _require_identity(user_identity)
    prompt = chat_request.prompt
    turn_started = datetime.datetime.now(datetime.timezone.utc)
    with Session(engine) as db_session:
        conversation = _conversation_or_404(
            db_session, identity, chat_request.conversation_id
        )
        if chat_request.regenerates:
            prompt, history = _prepare_regenerated_turn(
                db_session, identity, conversation
            )
        else:
            if prompt is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="The final chat message must be from the user",
                )
            history = _prepare_submitted_turn(
                db_session,
                conversation,
                prompt,
                image_file_part_from_ui_message(chat_request.messages[-1]),
                turn_started,
            )
    messages = [*history_from_transcript(history), prompt]

    message_id = str(uuid.uuid4())
    created_at = _utc_timestamp(turn_started)
    transcript = _TranscriptBuilder()

    async def event_stream() -> AsyncIterator[bytes]:
        text_part_id: str | None = None
        cookie = request.headers.get("cookie", "")
        yield _sse_event({"type": "start", "messageId": message_id})
        yield _sse_event(
            {
                "type": "message-metadata",
                "messageMetadata": {"createdAt": created_at},
            }
        )
        yield _sse_event({"type": "start-step"})

        try:
            async with httpx.AsyncClient(
                base_url=str(request.base_url),
                headers={"cookie": cookie},
            ) as client:
                tools = ThymisTools(client)
                try:
                    async for event in stream_chat(messages, model, tools):
                        if event["type"] == "text_delta":
                            if text_part_id is None:
                                text_part_id = f"text_{uuid.uuid4().hex}"
                                transcript.start_text()
                                yield _sse_event(
                                    {"type": "text-start", "id": text_part_id}
                                )
                            transcript.add_text(event["text"])
                            yield _sse_event(
                                {
                                    "type": "text-delta",
                                    "id": text_part_id,
                                    "delta": event["text"],
                                }
                            )
                        elif event["type"] == "tool_call":
                            if text_part_id is not None:
                                yield _sse_event(
                                    {"type": "text-end", "id": text_part_id}
                                )
                                text_part_id = None
                            transcript.end_text()
                            transcript.add_tool_call(
                                event["tool_call_id"],
                                event["tool_name"],
                                event["input"],
                            )
                            yield _sse_event(
                                {
                                    "type": "tool-input-available",
                                    "toolCallId": event["tool_call_id"],
                                    "toolName": event["tool_name"],
                                    "dynamic": True,
                                    "input": event["input"],
                                }
                            )
                        elif event["type"] == "tool_result":
                            transcript.add_tool_result(
                                event["tool_call_id"], event["output"]
                            )
                            yield _sse_event(
                                {
                                    "type": "tool-output-available",
                                    "toolCallId": event["tool_call_id"],
                                    "output": event["output"],
                                }
                            )
                        elif event["type"] == "entity_link":
                            if text_part_id is not None:
                                yield _sse_event(
                                    {"type": "text-end", "id": text_part_id}
                                )
                                text_part_id = None
                            transcript.end_text()
                            transcript.add_entity_link(event["entity"])
                            yield _sse_event(
                                {"type": "data-entity-link", "data": event["entity"]}
                            )
                except Exception:
                    logger.exception("Thymis assistant turn failed")
                    yield _sse_event(
                        {
                            "type": "error",
                            "errorText": "The assistant could not complete that request.",
                        }
                    )
                else:
                    if text_part_id is not None:
                        yield _sse_event({"type": "text-end", "id": text_part_id})
                    transcript.end_text()
                    yield _sse_event({"type": "finish-step"})
                    yield _sse_event({"type": "finish", "finishReason": "stop"})
        finally:
            _store_assistant_message(
                engine,
                identity,
                chat_request.conversation_id,
                message_id,
                transcript.parts,
                created_at,
            )
        yield _sse_done()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "x-vercel-ai-ui-message-stream": "v1",
        },
    )


def _store_assistant_message(
    engine: Engine,
    user_identity: str,
    conversation_id: uuid.UUID,
    message_id: str,
    parts: list[dict[str, Any]],
    created_at: str,
) -> None:
    """Persist the assistant reply, including partial output after a failure."""

    if not parts:
        return
    try:
        with Session(engine) as db_session:
            conversation = agent_conversation.get(
                db_session, user_identity, conversation_id
            )
            if conversation is None:
                return
            agent_conversation.append_messages(
                db_session,
                conversation,
                [_assistant_ui_message(message_id, parts, created_at)],
            )
    except Exception:
        logger.exception("Could not persist the Thymis assistant reply")
