"""Authenticated streaming endpoint and conversation store for the assistant."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from thymis_controller.agent_runtime import (
    ChatRequest,
    history_from_transcript,
    image_file_part_from_ui_message,
    stream_chat,
)
from thymis_controller.agent_tools import ThymisTools
from thymis_controller.config import global_settings
from thymis_controller.crud import agent_conversation
from thymis_controller.db_models import AgentConversation
from thymis_controller.dependencies import DBSessionAD, EngineAD, UserIdentityAD
from thymis_controller.models.agent import (
    AgentConversationDetail,
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
    db_session: DBSessionAD, user_identity: UserIdentityAD
) -> list[AgentConversationSummary]:
    """List the signed-in operator's saved assistant conversations."""

    identity = _require_identity(user_identity)
    return [
        _summary(db_session, conversation)
        for conversation in agent_conversation.list_for_user(db_session, identity)
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


def _attachment_filename(file_part: dict[str, Any] | None) -> str:
    """Take a stored filename from the browser's upload, minus any path."""
    filename = (file_part or {}).get("filename")
    if isinstance(filename, str) and filename.strip():
        return filename.strip().rsplit("/", 1)[-1].rsplit("\\", 1)[-1][:255]
    return DEFAULT_ATTACHMENT_FILENAME


def _user_ui_message(
    message_id: str,
    content: str,
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
    return {"id": message_id, "role": "user", "parts": parts}


def _assistant_ui_message(
    message_id: str, parts: list[dict[str, Any]]
) -> dict[str, Any]:
    return {"id": message_id, "role": "assistant", "parts": parts}


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

    identity = _require_identity(user_identity)
    prompt = chat_request.prompt
    file_part = image_file_part_from_ui_message(chat_request.messages[-1])
    attachment_filename = _attachment_filename(file_part)
    with Session(engine) as db_session:
        conversation = _conversation_or_404(
            db_session, identity, chat_request.conversation_id
        )
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
                filename=attachment_filename,
            )
            attachment_url = f"/api/agent/files/{stored_file.id}"
        agent_conversation.append_messages(
            db_session,
            conversation,
            [
                _user_ui_message(
                    str(uuid.uuid4()),
                    prompt.content,
                    attachment_url,
                    attachment_filename,
                )
            ],
        )
    messages = [*history_from_transcript(history), prompt]

    message_id = str(uuid.uuid4())
    transcript = _TranscriptBuilder()

    async def event_stream() -> AsyncIterator[bytes]:
        text_part_id: str | None = None
        cookie = request.headers.get("cookie", "")
        yield _sse_event({"type": "start", "messageId": message_id})
        yield _sse_event({"type": "start-step"})

        try:
            async with httpx.AsyncClient(
                base_url=str(request.base_url),
                headers={"cookie": cookie},
            ) as client:
                tools = ThymisTools(client)
                try:
                    async for event in stream_chat(
                        messages, global_settings.AGENT_MODEL, tools
                    ):
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
                [_assistant_ui_message(message_id, parts)],
            )
    except Exception:
        logger.exception("Could not persist the Thymis assistant reply")
