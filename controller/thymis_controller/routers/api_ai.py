import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
from thymis_controller.config import global_settings
from thymis_controller.dependencies import DBSessionAD
from thymis_controller.routers.auth import require_valid_user_session
from thymis_controller.task import controller as task_controller

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(require_valid_user_session)],
    tags=["ai-assistant"],
)


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    stream: bool = True
    model: str | None = None


class ChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[dict]


async def stream_openai_chat(
    api_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    messages: list[dict],
    project_path: str,
) -> AsyncGenerator[str, None]:
    """Stream responses from an OpenAI-compatible API."""
    import httpx

    url = f"{api_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": f"{system_prompt}\n\nProject path: {project_path}",
            },
            *messages,
        ],
        "stream": True,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        async with client.stream(
            "POST", url, json=payload, headers=headers
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                error_str = error_text.decode("utf-8", errors="replace")
                yield f'data: {{"error": {error_str}}}\n\n'
                return

            async for line in response.aiter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[len("data: ") :]
                if data_str == "[DONE]":
                    yield "data: [DONE]\n\n"
                    return
                try:
                    import json

                    data = json.loads(data_str)
                    if "choices" in data and data["choices"]:
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield f"data: {json.dumps({'content': content, 'role': 'assistant'})}\n\n"
                except (json.JSONDecodeError, KeyError):
                    continue


@router.post("/ai-assistant/chat")
async def chat(
    body: ChatRequest,
    _session=Depends(require_valid_user_session),
    db_session=Depends(DBSessionAD),
):
    """Chat with an AI assistant that knows about your Thymis project."""
    if not global_settings.AI_ASSISTANT_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="AI Assistant is not enabled. Set THYMIS_AI_ASSISTANT_ENABLED=true in your environment.",
        )
    if not global_settings.AI_ASSISTANT_API_KEY:
        raise HTTPException(
            status_code=400,
            detail="AI Assistant API key is not configured.",
        )

    model = body.model or global_settings.AI_ASSISTANT_MODEL

    # Convert messages to OpenAI format (strip Thymis role wrappers)
    messages = [{"role": msg.role, "content": msg.content} for msg in body.messages]

    project_path = str(global_settings.PROJECT_PATH)

    return EventSourceResponse(
        stream_openai_chat(
            api_url=global_settings.AI_ASSISTANT_API_URL,
            api_key=global_settings.AI_ASSISTANT_API_KEY,
            model=model,
            system_prompt=global_settings.AI_ASSISTANT_SYSTEM_PROMPT,
            messages=messages,
            project_path=project_path,
        ),
        media_type="text/event-stream",
    )


@router.get("/ai-assistant/status")
async def ai_status(
    _session=Depends(require_valid_user_session),
    db_session=Depends(DBSessionAD),
):
    """Check AI assistant configuration status."""
    return {
        "enabled": global_settings.AI_ASSISTANT_ENABLED,
        "api_url": global_settings.AI_ASSISTANT_API_URL,
        "api_key_configured": bool(global_settings.AI_ASSISTANT_API_KEY),
        "model": global_settings.AI_ASSISTANT_MODEL,
    }
