import asyncio

import httpx
import pytest
from pydantic import ValidationError
from pydantic_ai.models.test import TestModel
from thymis_controller.agent_runtime import (
    READ_ONLY_TOOL_NAMES,
    SYSTEM_INSTRUCTIONS,
    WRITE_TOOL_NAMES,
    ChatRequest,
    stream_chat,
)
from thymis_controller.agent_tools import ThymisTools


def make_tools() -> tuple[ThymisTools, httpx.AsyncClient]:
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
        base_url="https://controller.test",
    )
    return ThymisTools(client), client


def test_assistant_uses_existing_read_and_scoped_write_tool_schemas():
    async def scenario():
        tools, client = make_tools()
        model = TestModel(call_tools=[], custom_output_text="Fleet is healthy.")
        try:
            events = [
                event
                async for event in stream_chat(
                    ChatRequest(
                        messages=[{"role": "user", "content": "How is the fleet?"}]
                    ),
                    model,
                    tools,
                )
            ]
        finally:
            await client.aclose()

        assert (
            "".join(event["text"] for event in events if event["type"] == "text_delta")
            == "Fleet is healthy."
        )
        return {
            tool.name for tool in model.last_model_request_parameters.function_tools
        }

    tool_names = asyncio.run(scenario())

    assert tool_names <= READ_ONLY_TOOL_NAMES | WRITE_TOOL_NAMES
    assert {
        "get_state",
        "get_fleet_alerts",
        "get_device_metrics",
        "update_state",
        "build_device_image",
        "navigate_frontend",
        "manage_kiosk_display",
    } <= tool_names
    assert {
        "run_device_command",
        "list_secrets",
        "create_secret",
        "delete_artifact",
        "download_device_image",
    }.isdisjoint(tool_names)


def test_kiosk_display_prompt_uses_the_kiosk_i3_session():
    assert "manage_kiosk_display" in SYSTEM_INSTRUCTIONS
    assert "/run/user/$(id -u thymiskiosk)/i3/ipc-socket.*" in SYSTEM_INSTRUCTIONS
    assert "i3-msg" in SYSTEM_INSTRUCTIONS
    assert "systemctl restart display-manager.service" in SYSTEM_INSTRUCTIONS


def test_chat_request_rejects_a_non_user_final_message():
    with pytest.raises(ValidationError, match="final chat message"):
        ChatRequest(messages=[{"role": "assistant", "content": "Hello"}])


def test_chat_request_accepts_ai_sdk_ui_messages():
    request = ChatRequest(
        messages=[
            {
                "role": "assistant",
                "parts": [{"type": "text", "text": "Prior response"}],
            },
            {
                "role": "user",
                "parts": [{"type": "text", "text": "How is the fleet?"}],
            },
        ]
    )

    assert [(message.role, message.content) for message in request.messages] == [
        ("assistant", "Prior response"),
        ("user", "How is the fleet?"),
    ]


def test_chat_request_accepts_a_final_vnc_screenshot():
    request = ChatRequest(
        messages=[
            {
                "role": "user",
                "parts": [
                    {"type": "text", "text": "What is visible?"},
                    {
                        "type": "file",
                        "mediaType": "image/png",
                        "filename": "vnc-device.png",
                        "url": "data:image/png;base64,c2NyZWVuc2hvdA==",
                    },
                ],
            }
        ]
    )

    assert request.messages[-1].screenshot == b"screenshot"


def test_chat_request_rejects_a_non_png_vnc_screenshot():
    with pytest.raises(ValidationError, match="PNG data URL"):
        ChatRequest(
            messages=[
                {
                    "role": "user",
                    "content": "What is visible?",
                    "screenshot": "data:image/jpeg;base64,c2NyZWVuc2hvdA==",
                }
            ]
        )


def test_stream_chat_accepts_a_vnc_screenshot():
    async def scenario():
        tools, client = make_tools()
        model = TestModel(
            call_tools=[], custom_output_text="The screenshot is visible."
        )
        try:
            return [
                event
                async for event in stream_chat(
                    ChatRequest(
                        messages=[
                            {
                                "role": "user",
                                "content": "What is visible?",
                                "screenshot": "data:image/png;base64,c2NyZWVuc2hvdA==",
                            }
                        ]
                    ),
                    model,
                    tools,
                )
            ]
        finally:
            await client.aclose()

    events = asyncio.run(scenario())
    assert (
        "".join(event["text"] for event in events if event["type"] == "text_delta")
        == "The screenshot is visible."
    )
