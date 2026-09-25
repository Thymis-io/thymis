"""PydanticAI runtime for the Thymis operator chat assistant."""

from __future__ import annotations

import base64
import binascii
import uuid
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, Field, JsonValue, field_validator, model_validator
from pydantic_ai import Agent, Tool
from pydantic_ai.messages import (
    BinaryContent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ModelMessage,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    UserPromptPart,
)
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from thymis_controller.agent_tools import ThymisTools
from thymis_controller.agent_tools.registry import RegisteredTool

SYSTEM_INSTRUCTIONS = """You are the Thymis Assistant for NixOS device operators.
Use the available tools to inspect current controller state before making factual
claims about devices, configurations, tasks, or fleet health. You may make a
requested controller change or queue an action. Before a state-changing tool,
briefly state the target and intended effect; only report success after its tool
result confirms it. For a device-image download request, use build_device_image:
it queues the dashboard's image build, and the signed-in browser downloads the
image automatically only after that build task succeeds. When mentioning a specific
configuration, tag, device, or task, call link_entity after verifying it so the
operator receives a first-class entity link.

Treat every controller as a production system. Use read-only diagnostic tools to
investigate proactively, but use a state-changing tool only for an explicit request
from the operator in this conversation. Never infer authorization to deploy, build,
commit, update a project, change controller state or configuration, restart a device
or display manager, or enable automatic updates from a diagnosis or a suggested
remedy. If the operator has not explicitly requested the change, explain the
proposed action and its impact, then ask them to request it.

For a device configured with the Thymis Kiosk module, use manage_kiosk_display for
display diagnosis and explicit graphical-session actions. inspect_i3_outputs finds
the active i3 IPC socket under /run/user/$(id -u thymiskiosk)/i3/ipc-socket.* and
asks i3-msg for the current output state. read_i3_config asks that same live i3
session for its active configuration. Before opening a browser window, call
read_i3_config and inspect its completed task output to find the exact Chromium
binary path from the configured i3 exec command; do not guess a system-profile path.
run_x_command sends the requested command through i3's exec facility, so i3 runs it
in the thymiskiosk graphical-session context rather than as root. Use it only for an
explicit operator request, such as opening a browser window at a stated URL.
inspect_logs reads the current boot's display-manager and thymiskiosk-session
journals. restart_display_manager runs systemctl restart display-manager.service,
which ends the graphical session; use it only when the operator explicitly requests
a restart or after discussing that effect. After every display operation, inspect its
task output before reporting the result. Never access secrets, use generic arbitrary
root commands, or delete records. State uncertainty plainly and give operators a
concrete next step when an operation cannot be completed."""

# The assistant uses the existing authenticated controller API boundary. These
# tools intentionally omit secret access, arbitrary root commands, and permanent
# deletion; all other mutations are applied as the current signed-in operator.
READ_ONLY_TOOL_NAMES = frozenset(
    {
        "get_state",
        "link_entity",
        "list_available_modules",
        "get_configuration",
        "list_deployment_infos",
        "get_deployment_info",
        "list_hardware_devices",
        "get_device_connection_history",
        "get_device_metrics",
        "get_device_error_logs",
        "list_tasks",
        "get_task",
        "list_artifacts",
        "get_history",
        "get_history_diff",
        "get_repo_status",
        "get_logs",
        "list_log_program_names",
        "get_fleet_connectivity",
        "get_fleet_metrics_latest",
        "get_fleet_availability",
        "get_fleet_alerts",
        "get_controller_settings",
        "get_external_repository_status",
        "get_external_repository_flake_ref",
        "list_external_repository_branches",
        "list_external_repository_tags",
        "check_external_repository_prefetch",
        "check_external_repository_api_access",
    }
)
WRITE_TOOL_NAMES = frozenset(
    {
        "update_state",
        "patch_configuration_field",
        "update_deployment_info",
        "cancel_task",
        "retry_task",
        "upload_artifacts",
        "rename_artifact",
        "update_controller_settings",
        "build_project",
        "deploy",
        "build_device_image",
        "restart_device",
        "switch_device_config",
        "commit",
        "update_project",
        "auto_update",
        "navigate_frontend",
        "manage_kiosk_display",
    }
)

ASSISTANT_TOOL_NAMES = READ_ONLY_TOOL_NAMES | WRITE_TOOL_NAMES

MAX_SCREENSHOT_SIZE_BYTES = 6 * 1024 * 1024


class ChatMessage(BaseModel):
    """A browser chat message with an optional current VNC screenshot."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12_000)
    screenshot: bytes | None = None

    @field_validator("screenshot", mode="before")
    @classmethod
    def decode_vnc_screenshot(cls, value: Any) -> bytes | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            image = value
        elif isinstance(value, str) and value.startswith("data:image/png;base64,"):
            encoded_image = value.removeprefix("data:image/png;base64,")
            maximum_encoded_size = (MAX_SCREENSHOT_SIZE_BYTES * 4) // 3 + 4
            if len(encoded_image) > maximum_encoded_size:
                raise ValueError("VNC screenshots must not exceed 6 MiB")
            try:
                image = base64.b64decode(encoded_image, validate=True)
            except (binascii.Error, ValueError) as error:
                raise ValueError(
                    "VNC screenshot must be a base64 PNG data URL"
                ) from error
        else:
            raise ValueError("VNC screenshot must be a PNG data URL")

        if len(image) > MAX_SCREENSHOT_SIZE_BYTES:
            raise ValueError("VNC screenshots must not exceed 6 MiB")
        return image


def text_from_ui_message(message: Any) -> str:
    """Extract the visible text of one AI SDK UI message."""
    if isinstance(message, str):
        return message
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content
    parts = message.get("parts")
    if not isinstance(parts, list):
        return ""
    return "".join(
        part["text"]
        for part in parts
        if isinstance(part, dict)
        and part.get("type") == "text"
        and isinstance(part.get("text"), str)
    )


def image_file_part_from_ui_message(message: Any) -> dict[str, Any] | None:
    """Return the image attachment the browser just uploaded for one message.

    Only inline ``data:`` attachments count: a stored conversation references its
    attachments by URL, and replaying one must never store it again.
    """
    if not isinstance(message, dict):
        return None
    parts = message.get("parts")
    if not isinstance(parts, list):
        return None
    return next(
        (
            part
            for part in parts
            if isinstance(part, dict)
            and part.get("type") == "file"
            and part.get("mediaType") == "image/png"
            and isinstance(part.get("url"), str)
            and part["url"].startswith("data:")
        ),
        None,
    )


def screenshot_from_ui_message(message: Any) -> str | None:
    """Extract an inline PNG data URL attached to one AI SDK UI message.

    A stored conversation links its attachments instead of embedding them, so
    anything that is not an inline data URL is not model input.
    """
    if not isinstance(message, dict):
        return None
    parts = message.get("parts")
    urls = [message.get("screenshot")]
    if isinstance(parts, list):
        urls.extend(
            part.get("url")
            for part in parts
            if isinstance(part, dict)
            and part.get("type") == "file"
            and part.get("mediaType") == "image/png"
        )
    return next(
        (url for url in urls if isinstance(url, str) and url.startswith("data:")),
        None,
    )


def chat_message_from_ui_message(message: Any) -> ChatMessage | None:
    """Normalize one AI SDK UI message into a model-facing chat message.

    Returns ``None`` when the message carries no user-visible text, such as an
    assistant turn that only called tools.
    """
    if not isinstance(message, dict):
        raise ValueError("Chat messages must be objects")
    role = message.get("role")
    if role not in ("user", "assistant"):
        raise ValueError("Chat message roles must be 'user' or 'assistant'")
    content = message.get("content")
    if not isinstance(content, str):
        content = text_from_ui_message(message)
    if not content.strip():
        return None
    if role == "user":
        screenshot = screenshot_from_ui_message(message)
        if screenshot is not None:
            # Attaching the data URL re-runs the screenshot field validator.
            return ChatMessage(role=role, content=content, screenshot=screenshot)
    return ChatMessage(role=role, content=content)


def history_from_transcript(transcript: list[Any]) -> list[ChatMessage]:
    """Rebuild prior conversation turns from persisted AI SDK UI messages.

    Persisted history is text-only: a screenshot is one-shot model input that is
    never stored, so it is deliberately not replayed here.
    """
    history: list[ChatMessage] = []
    for message in transcript:
        chat_message = chat_message_from_ui_message(message)
        if chat_message is None:
            continue
        history.append(
            ChatMessage(role=chat_message.role, content=chat_message.content)
        )
    return history


class ChatRequest(BaseModel):
    """One browser chat turn of a persisted conversation.

    The AI SDK UI transport always sends the whole message array it holds; only
    the final entry of a submitted turn is a new prompt, because the conversation
    history comes from the controller database instead of the browser. A
    regenerated turn re-runs the prompt that is already stored, so the array
    carries no new prompt at all.
    """

    conversation_id: uuid.UUID
    messages: list[JsonValue] = Field(min_length=1, max_length=2_000)
    trigger: Literal["submit-message", "regenerate-message"] = "submit-message"

    @model_validator(mode="after")
    def requires_final_user_message(self) -> ChatRequest:
        if self.regenerates:
            return self
        message = chat_message_from_ui_message(self.messages[-1])
        if message is None:
            raise ValueError("The final chat message must contain text")
        if message.role != "user":
            raise ValueError("The final chat message must be from the user")
        return self

    @property
    def regenerates(self) -> bool:
        """Whether this turn re-runs the stored trailing user prompt."""
        return self.trigger == "regenerate-message"

    @property
    def prompt(self) -> ChatMessage | None:
        """The new user prompt that ends a submitted turn."""
        message = chat_message_from_ui_message(self.messages[-1])
        if message is None or message.role != "user":
            return None
        return message


def _to_message_history(messages: list[ChatMessage]) -> list[ModelMessage]:
    """Build safe model history without accepting browser-supplied system parts."""

    history: list[ModelMessage] = []
    for message in messages[:-1]:
        if message.role == "user":
            history.append(
                ModelRequest(parts=[UserPromptPart(content=message.content)])
            )
        else:
            history.append(
                ModelResponse(
                    parts=[TextPart(content=message.content)], model_name="thymis-ui"
                )
            )
    return history


def _as_pydantic_tool(registered_tool: RegisteredTool) -> Tool:
    """Adapt one existing typed Thymis tool without duplicating its JSON schema."""

    definition = registered_tool.definition()

    async def invoke(**arguments: Any) -> Any:
        return await registered_tool.invoke(arguments)

    return Tool.from_schema(
        invoke,
        name=definition.name,
        description=definition.description,
        json_schema=definition.input_schema,
        sequential=True,
    )


GATEWAY_PROVIDER_NAMES = frozenset({"openai", "openai-chat", "gateway"})


@lru_cache(maxsize=8)
def _gateway_model(model_name: str, base_url: str, api_key: str | None) -> Model:
    """Build one reusable client for an OpenAI-compatible gateway."""
    return OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(base_url=base_url, api_key=api_key),
    )


def resolve_model(
    model: str | Model,
    base_url: str | None = None,
    api_key: str | None = None,
) -> str | Model:
    """Resolve the configured model, honouring an OpenAI-compatible gateway.

    Without a base URL the model string goes to PydanticAI unchanged, so provider
    prefixes such as ``openrouter:`` keep working. With one, the request has to
    reach that gateway instead of the public OpenAI endpoint that a bare
    ``openai:`` prefix would select.
    """
    if isinstance(model, Model) or not base_url:
        return model

    provider_name, separator, model_name = model.partition(":")
    if not separator:
        provider_name, model_name = "", model
    if provider_name and provider_name not in GATEWAY_PROVIDER_NAMES:
        raise ValueError(
            "THYMIS_AGENT_BASE_URL requires an OpenAI-compatible THYMIS_AGENT_MODEL "
            f"(for example openai:<model-id>), not {provider_name!r}"
        )
    return _gateway_model(model_name, base_url, api_key or None)


def build_agent(model: str | Model, tools: ThymisTools) -> Agent[None, str]:
    """Create a per-request agent bound to one authenticated tool client."""

    registered_tools = tools.registered_tools()
    selected_tools = [
        _as_pydantic_tool(registered_tool)
        for name, registered_tool in registered_tools.items()
        if name in ASSISTANT_TOOL_NAMES
    ]
    return Agent(model, instructions=SYSTEM_INSTRUCTIONS, tools=selected_tools)


async def stream_chat(
    messages: list[ChatMessage],
    model: str | Model,
    tools: ThymisTools,
) -> AsyncIterator[dict[str, Any]]:
    """Yield browser-safe stream events while the Python agent handles one turn.

    ``messages`` is the persisted conversation history followed by the new user
    prompt, so the model never sees browser-supplied prior turns.
    """

    agent = build_agent(model, tools)
    history = _to_message_history(messages)
    final_message = messages[-1]
    prompt = final_message.content
    if final_message.screenshot is not None:
        prompt = [
            prompt,
            BinaryContent(data=final_message.screenshot, media_type="image/png"),
        ]

    async with agent.run_stream_events(prompt, message_history=history) as events:
        async for event in events:
            if isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                if event.part.content:
                    yield {"type": "text_delta", "text": event.part.content}
            elif isinstance(event, PartDeltaEvent) and isinstance(
                event.delta, TextPartDelta
            ):
                if event.delta.content_delta:
                    yield {"type": "text_delta", "text": event.delta.content_delta}
            elif isinstance(event, FunctionToolCallEvent):
                if event.part.tool_name == "link_entity":
                    continue
                yield {
                    "type": "tool_call",
                    "tool_call_id": event.tool_call_id,
                    "tool_name": event.part.tool_name,
                    "input": event.part.args_as_dict(),
                }
            elif isinstance(event, FunctionToolResultEvent):
                if event.part.tool_name == "link_entity":
                    if isinstance(event.part.content, dict):
                        yield {"type": "entity_link", "entity": event.part.content}
                    continue
                yield {
                    "type": "tool_result",
                    "tool_call_id": event.tool_call_id,
                    "tool_name": event.part.tool_name,
                    "output": {},
                }


__all__ = [
    "READ_ONLY_TOOL_NAMES",
    "WRITE_TOOL_NAMES",
    "ChatMessage",
    "ChatRequest",
    "build_agent",
    "chat_message_from_ui_message",
    "history_from_transcript",
    "resolve_model",
    "image_file_part_from_ui_message",
    "stream_chat",
    "text_from_ui_message",
]
