"""Authenticated streaming endpoint for the Thymis chat assistant."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from thymis_controller.agent_runtime import ChatRequest, stream_chat
from thymis_controller.agent_tools import ThymisTools
from thymis_controller.config import global_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])


def _sse_event(payload: dict[str, object]) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False, separators=(',', ':'))}\n\n".encode(
        "utf-8"
    )


def _sse_done() -> bytes:
    return b"data: [DONE]\n\n"


@router.post("/agent/chat")
async def chat(request: Request, chat_request: ChatRequest) -> StreamingResponse:
    """Stream one assistant turn for the current signed-in operator."""

    if not global_settings.AGENT_MODEL:
        raise HTTPException(
            status_code=503,
            detail="Assistant is not configured. Set THYMIS_AGENT_MODEL and its provider credentials.",
        )

    async def event_stream() -> AsyncIterator[bytes]:
        message_id = f"msg_{uuid.uuid4().hex}"
        text_part_id: str | None = None
        cookie = request.headers.get("cookie", "")
        yield _sse_event({"type": "start", "messageId": message_id})
        yield _sse_event({"type": "start-step"})

        async with httpx.AsyncClient(
            base_url=str(request.base_url),
            headers={"cookie": cookie},
        ) as client:
            tools = ThymisTools(client)
            try:
                async for event in stream_chat(
                    chat_request, global_settings.AGENT_MODEL, tools
                ):
                    if event["type"] == "text_delta":
                        if text_part_id is None:
                            text_part_id = f"text_{uuid.uuid4().hex}"
                            yield _sse_event({"type": "text-start", "id": text_part_id})
                        yield _sse_event(
                            {
                                "type": "text-delta",
                                "id": text_part_id,
                                "delta": event["text"],
                            }
                        )
                    elif event["type"] == "tool_call":
                        if text_part_id is not None:
                            yield _sse_event({"type": "text-end", "id": text_part_id})
                            text_part_id = None
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
                        yield _sse_event(
                            {
                                "type": "tool-output-available",
                                "toolCallId": event["tool_call_id"],
                                "output": event["output"],
                            }
                        )
                    elif event["type"] == "entity_link":
                        if text_part_id is not None:
                            yield _sse_event({"type": "text-end", "id": text_part_id})
                            text_part_id = None
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
                yield _sse_event({"type": "finish-step"})
                yield _sse_event({"type": "finish", "finishReason": "stop"})
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
