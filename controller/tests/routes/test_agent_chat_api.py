import json
from unittest import mock

from thymis_controller.config import global_settings
from thymis_controller.routers import api_agent


def test_chat_endpoint_requires_an_agent_model(test_client):
    with mock.patch.object(global_settings, "AGENT_MODEL", None):
        response = test_client.post(
            "/api/agent/chat",
            json={"messages": [{"role": "user", "content": "How is the fleet?"}]},
        )

    assert response.status_code == 503
    assert response.json()["detail"].startswith("Assistant is not configured")


def test_chat_endpoint_emits_an_ai_sdk_ui_message_stream(test_client):
    async def fake_stream_chat(*_args):
        yield {"type": "text_delta", "text": "Fleet "}
        yield {
            "type": "tool_call",
            "tool_call_id": "call_1",
            "tool_name": "get_state",
            "input": {},
        }
        yield {
            "type": "tool_result",
            "tool_call_id": "call_1",
            "tool_name": "get_state",
            "output": {},
        }
        yield {"type": "text_delta", "text": "is healthy."}
        yield {
            "type": "entity_link",
            "entity": {
                "entityType": "task",
                "identifier": "task-1",
                "label": "build-device-image",
            },
        }

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", fake_stream_chat),
    ):
        response = test_client.post(
            "/api/agent/chat",
            json={"messages": [{"role": "user", "content": "How is the fleet?"}]},
        )

    assert response.status_code == 200
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: {")
    ]
    assert [event["type"] for event in events] == [
        "start",
        "start-step",
        "text-start",
        "text-delta",
        "text-end",
        "tool-input-available",
        "tool-output-available",
        "text-start",
        "text-delta",
        "text-end",
        "data-entity-link",
        "finish-step",
        "finish",
    ]
    assert (
        "".join(event["delta"] for event in events if event["type"] == "text-delta")
        == "Fleet is healthy."
    )
    assert (
        next(event for event in events if event["type"] == "tool-input-available")[
            "dynamic"
        ]
        is True
    )
    assert next(event for event in events if event["type"] == "data-entity-link")[
        "data"
    ] == {
        "entityType": "task",
        "identifier": "task-1",
        "label": "build-device-image",
    }
    assert response.text.endswith("data: [DONE]\n\n")
