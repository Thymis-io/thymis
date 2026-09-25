import json
import uuid
from unittest import mock

from thymis_controller.config import global_settings
from thymis_controller.crud import web_session
from thymis_controller.db_models import AgentFile
from thymis_controller.routers import api_agent


def login(test_client, db_session, email: str) -> None:
    """Create a real web session row and sign the test client in as that user."""
    session = web_session.create(db_session, username=email.split("@")[0], email=email)
    test_client.cookies.clear()
    test_client.cookies.update(
        {"session-id": str(session.id), "session-token": session.session_token}
    )


def open_conversation(test_client) -> str:
    response = test_client.post("/api/agent/conversations")
    assert response.status_code == 201, response.text
    return response.json()["id"]


def chat_body(conversation_id: str, prompt: str = "How is the fleet?") -> dict:
    return {
        "conversation_id": conversation_id,
        "messages": [{"role": "user", "content": prompt}],
    }


def fake_stream_chat(*_args, **_kwargs):
    async def events():
        yield {"type": "thinking_delta", "text": "Checking the fleet first."}
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
            "output": {"devices": 0, "connected": 0},
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

    return events()


def stream_events(response) -> list[dict]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: {")
    ]


def test_chat_endpoint_requires_an_agent_model(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    with mock.patch.object(global_settings, "AGENT_MODEL", None):
        response = test_client.post("/api/agent/chat", json=chat_body(conversation_id))

    assert response.status_code == 503
    assert response.json()["detail"].startswith("Assistant is not configured")


def test_conversations_require_a_signed_in_identity(test_client):
    assert test_client.get("/api/agent/conversations").status_code == 401
    assert test_client.post("/api/agent/conversations").status_code == 401


def test_conversations_are_scoped_to_one_operator(test_client, db_session):
    login(test_client, db_session, "alice@example.com")
    conversation_id = open_conversation(test_client)

    detail = test_client.get(f"/api/agent/conversations/{conversation_id}")
    assert detail.status_code == 200
    assert {
        key: detail.json()[key] for key in ("id", "title", "message_count", "messages")
    } == {
        "id": conversation_id,
        "title": "New chat",
        "message_count": 0,
        "messages": [],
    }

    listed = test_client.get("/api/agent/conversations").json()
    assert [conversation["id"] for conversation in listed] == [conversation_id]
    assert listed[0]["title"] == "New chat"
    assert listed[0]["message_count"] == 0

    login(test_client, db_session, "bob@example.com")
    assert test_client.get("/api/agent/conversations").json() == []
    assert (
        test_client.get(f"/api/agent/conversations/{conversation_id}").status_code
        == 404
    )
    assert (
        test_client.delete(f"/api/agent/conversations/{conversation_id}").status_code
        == 404
    )

    login(test_client, db_session, "alice@example.com")
    assert (
        test_client.delete(f"/api/agent/conversations/{conversation_id}").status_code
        == 204
    )
    assert test_client.get("/api/agent/conversations").json() == []
    assert (
        test_client.get(f"/api/agent/conversations/{conversation_id}").status_code
        == 404
    )


def test_chat_endpoint_emits_an_ai_sdk_ui_message_stream(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", fake_stream_chat),
    ):
        response = test_client.post("/api/agent/chat", json=chat_body(conversation_id))

    assert response.status_code == 200
    assert response.headers["x-vercel-ai-ui-message-stream"] == "v1"
    events = stream_events(response)
    assert [event["type"] for event in events] == [
        "start",
        "message-metadata",
        "start-step",
        "reasoning-start",
        "reasoning-delta",
        "reasoning-end",
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
    assert (
        next(event for event in events if event["type"] == "reasoning-delta")["delta"]
        == "Checking the fleet first."
    )
    assert next(event for event in events if event["type"] == "tool-output-available")[
        "output"
    ] == {"devices": 0, "connected": 0}
    assert next(event for event in events if event["type"] == "data-entity-link")[
        "data"
    ] == {
        "entityType": "task",
        "identifier": "task-1",
        "label": "build-device-image",
    }
    assert response.text.endswith("data: [DONE]\n\n")


def test_chat_persists_the_turn_as_replayable_ui_messages(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", fake_stream_chat),
    ):
        response = test_client.post("/api/agent/chat", json=chat_body(conversation_id))
    assert response.status_code == 200
    assistant_id = stream_events(response)[0]["messageId"]

    detail = test_client.get(f"/api/agent/conversations/{conversation_id}").json()
    assert detail["title"] == "How is the fleet?"
    assert detail["message_count"] == 2
    user_message, assistant_message = detail["messages"]

    assert user_message["role"] == "user"
    assert user_message["parts"] == [{"type": "text", "text": "How is the fleet?"}]
    assert (
        user_message["metadata"]["createdAt"]
        == assistant_message["metadata"]["createdAt"]
    )
    assert assistant_message["metadata"]["createdAt"].endswith("Z")
    assert {
        key: value for key, value in assistant_message.items() if key != "metadata"
    } == {
        "id": assistant_id,
        "role": "assistant",
        "parts": [
            {"type": "reasoning", "text": "Checking the fleet first."},
            {"type": "text", "text": "Fleet "},
            {
                "type": "dynamic-tool",
                "toolCallId": "call_1",
                "toolName": "get_state",
                "state": "output-available",
                "input": {},
                "output": {"devices": 0, "connected": 0},
            },
            {"type": "text", "text": "is healthy."},
            {
                "type": "data-entity-link",
                "data": {
                    "entityType": "task",
                    "identifier": "task-1",
                    "label": "build-device-image",
                },
            },
        ],
    }

    listed = test_client.get("/api/agent/conversations").json()
    assert [conversation["id"] for conversation in listed] == [conversation_id]
    assert listed[0]["message_count"] == 2


def test_chat_stores_attached_screenshots_and_serves_them_to_the_owner(
    test_client, db_session
):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)
    prompts: list[list] = []

    def record_stream_chat(messages, *_args, **_kwargs):
        prompts.append(messages)
        return fake_stream_chat()

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", record_stream_chat),
    ):
        response = test_client.post(
            "/api/agent/chat",
            json={
                "conversation_id": conversation_id,
                "messages": [
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
                ],
            },
        )
    assert response.status_code == 200
    # The model still receives the screenshot for the turn that attached it.
    assert prompts[0][-1].screenshot == b"screenshot"

    detail = test_client.get(f"/api/agent/conversations/{conversation_id}").json()
    parts = detail["messages"][0]["parts"]
    assert parts[0] == {"type": "text", "text": "What is visible?"}
    file_part = parts[1]
    assert file_part["mediaType"] == "image/png"
    assert file_part["filename"] == "vnc-device.png"
    assert file_part["url"].startswith("/api/agent/files/")
    assert "data:" not in file_part["url"]

    image = test_client.get(file_part["url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert image.headers["cache-control"] == "private, no-store"
    assert image.content == b"screenshot"

    login(test_client, db_session, "bob@example.com")
    assert test_client.get(file_part["url"]).status_code == 404


def test_deleting_a_conversation_removes_its_attachments(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", fake_stream_chat),
    ):
        response = test_client.post(
            "/api/agent/chat",
            json={
                "conversation_id": conversation_id,
                "messages": [
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
                ],
            },
        )
    assert response.status_code == 200
    detail = test_client.get(f"/api/agent/conversations/{conversation_id}").json()
    file_url = detail["messages"][0]["parts"][1]["url"]

    assert (
        test_client.delete(f"/api/agent/conversations/{conversation_id}").status_code
        == 204
    )
    assert test_client.get(file_url).status_code == 404
    assert (
        db_session.query(AgentFile)
        .filter_by(id=uuid.UUID(file_url.rsplit("/", 1)[-1]))
        .first()
        is None
    )


def test_chat_replays_the_stored_transcript_as_model_history(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)
    calls: list[list] = []

    def record_stream_chat(messages, *_args, **_kwargs):
        calls.append([(message.role, message.content) for message in messages])
        return fake_stream_chat()

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", record_stream_chat),
    ):
        for prompt in ("How is the fleet?", "And now?"):
            response = test_client.post(
                "/api/agent/chat", json=chat_body(conversation_id, prompt)
            )
            assert response.status_code == 200

    assert calls == [
        [("user", "How is the fleet?")],
        [
            ("user", "How is the fleet?"),
            ("assistant", "Fleet is healthy."),
            ("user", "And now?"),
        ],
    ]


def test_chat_regenerates_the_trailing_turn_without_duplicating_the_prompt(
    test_client, db_session
):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)
    calls: list[list] = []

    def record_stream_chat(messages, *_args, **_kwargs):
        calls.append([(message.role, message.content) for message in messages])
        return fake_stream_chat()

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", record_stream_chat),
    ):
        first = test_client.post("/api/agent/chat", json=chat_body(conversation_id))
        assert first.status_code == 200
        regenerated = test_client.post(
            "/api/agent/chat",
            json={
                **chat_body(conversation_id),
                "trigger": "regenerate-message",
            },
        )
    assert regenerated.status_code == 200

    # The retried turn sees the same prompt, and the replaced reply is not kept.
    assert calls == [
        [("user", "How is the fleet?")],
        [("user", "How is the fleet?")],
    ]
    detail = test_client.get(f"/api/agent/conversations/{conversation_id}").json()
    assert detail["message_count"] == 2
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant"]


def test_chat_regenerates_the_stored_screenshot_of_the_trailing_turn(
    test_client, db_session
):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)
    prompts: list[list] = []

    def record_stream_chat(messages, *_args, **_kwargs):
        prompts.append(messages)
        return fake_stream_chat()

    with (
        mock.patch.object(global_settings, "AGENT_MODEL", "test-model"),
        mock.patch.object(api_agent, "stream_chat", record_stream_chat),
    ):
        first = test_client.post(
            "/api/agent/chat",
            json={
                "conversation_id": conversation_id,
                "messages": [
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
                ],
            },
        )
        assert first.status_code == 200
        regenerated = test_client.post(
            "/api/agent/chat",
            json={
                "conversation_id": conversation_id,
                "messages": [{"role": "assistant", "parts": []}],
                "trigger": "regenerate-message",
            },
        )
    assert regenerated.status_code == 200
    # The retry re-attaches the stored screenshot instead of losing it.
    assert prompts[1][-1].screenshot == b"screenshot"


def test_chat_rejects_regenerating_an_empty_conversation(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    with mock.patch.object(global_settings, "AGENT_MODEL", "test-model"):
        response = test_client.post(
            "/api/agent/chat",
            json={
                "conversation_id": conversation_id,
                "messages": [{"role": "assistant", "parts": []}],
                "trigger": "regenerate-message",
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "This conversation has no turn to regenerate"


def test_conversations_can_be_renamed_and_searched(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    renamed = test_client.patch(
        f"/api/agent/conversations/{conversation_id}",
        json={"title": "  Fleet triage  "},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Fleet triage"

    assert [
        conversation["id"]
        for conversation in test_client.get(
            "/api/agent/conversations", params={"q": "triage"}
        ).json()
    ] == [conversation_id]
    assert (
        test_client.get("/api/agent/conversations", params={"q": "unrelated"}).json()
        == []
    )
    assert (
        test_client.patch(
            f"/api/agent/conversations/{conversation_id}", json={"title": "   "}
        ).status_code
        == 422
    )


def test_chat_rejects_an_unknown_conversation(test_client, db_session):
    login(test_client, db_session, "operator@example.com")

    with mock.patch.object(global_settings, "AGENT_MODEL", "test-model"):
        response = test_client.post(
            "/api/agent/chat", json=chat_body(str(uuid.uuid4()))
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_chat_requires_a_final_user_prompt(test_client, db_session):
    login(test_client, db_session, "operator@example.com")
    conversation_id = open_conversation(test_client)

    response = test_client.post(
        "/api/agent/chat",
        json={
            "conversation_id": conversation_id,
            "messages": [{"role": "assistant", "content": "Hello"}],
        },
    )

    assert response.status_code == 422
