import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError
from thymis_controller.agent_tools import ThymisToolError, ThymisTools, UnknownToolError


def make_tools(handler):
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="https://controller.test"
    )
    return ThymisTools(client), client


def test_definitions_cover_frontend_entities_and_actions():
    async def scenario():
        tools, client = make_tools(lambda request: httpx.Response(500, request=request))
        try:
            definitions = {
                definition.name: definition for definition in tools.definitions()
            }
        finally:
            await client.aclose()

        assert {
            "get_state",
            "update_state",
            "list_available_modules",
            "list_deployment_infos",
            "list_tasks",
            "list_secrets",
            "list_artifacts",
            "get_logs",
            "build_project",
            "deploy",
            "build_device_image",
            "restart_device",
            "switch_device_config",
            "commit",
            "update_project",
            "auto_update",
        } <= definitions.keys()
        assert definitions["deploy"].input_schema["additionalProperties"] is False
        assert definitions["deploy"].input_schema["properties"] == {
            "config_identifiers": {
                "items": {"type": "string"},
                "title": "Config Identifiers",
                "type": "array",
            },
            "deployment_info_ids": {
                "items": {"format": "uuid", "type": "string"},
                "title": "Deployment Info Ids",
                "type": "array",
            },
        }

    asyncio.run(scenario())


def test_invoke_maps_typed_device_and_deploy_arguments_to_controller_api():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True}, request=request)

    async def scenario():
        tools, client = make_tools(handler)
        try:
            deployment_info_id = "69e2a620-7534-442c-a8a8-2b1eb8d9be87"
            assert await tools.invoke(
                "update_deployment_info",
                {
                    "deployment_info_id": deployment_info_id,
                    "changes": {"location": None, "notes": "rack B"},
                },
            ) == {"ok": True}
            assert await tools.invoke(
                "deploy",
                {
                    "config_identifiers": ["camera", "kiosk"],
                    "deployment_info_ids": [deployment_info_id],
                },
            ) == {"ok": True}
        finally:
            await client.aclose()

    asyncio.run(scenario())

    update_request, deploy_request = requests
    assert update_request.method == "PATCH"
    assert (
        update_request.url.path
        == "/api/deployment_info/69e2a620-7534-442c-a8a8-2b1eb8d9be87"
    )
    assert json.loads(update_request.content) == {"location": None, "notes": "rack B"}
    assert deploy_request.method == "POST"
    assert deploy_request.url.params.get_list("config") == ["camera", "kiosk"]
    assert deploy_request.url.params.get_list("deployment_info_id") == [
        "69e2a620-7534-442c-a8a8-2b1eb8d9be87"
    ]


def test_upload_artifacts_encodes_multipart_and_rejects_invalid_base64():
    received = []

    def handler(request):
        received.append(request)
        return httpx.Response(
            200, json={"message": "Artifacts created"}, request=request
        )

    async def scenario():
        tools, client = make_tools(handler)
        try:
            result = await tools.invoke(
                "upload_artifacts",
                {
                    "artifacts": [
                        {"name": "settings.json", "content_base64": "eyJvayI6IHRydWV9"}
                    ]
                },
            )
            with pytest.raises(ValueError, match="not valid base64"):
                await tools.invoke(
                    "upload_artifacts",
                    {"artifacts": [{"name": "bad", "content_base64": "not-base64"}]},
                )
            return result
        finally:
            await client.aclose()

    assert asyncio.run(scenario()) == {"message": "Artifacts created"}
    assert received[0].url.path == "/api/artifacts/"
    assert b'filename="settings.json"' in received[0].content
    assert b'{"ok": true}' in received[0].content


def test_invoke_reports_api_failures_and_rejects_unknown_or_extra_arguments():
    def handler(request):
        return httpx.Response(
            409,
            json={"detail": "Repository is dirty. Please commit your changes first."},
            request=request,
        )

    async def scenario():
        tools, client = make_tools(handler)
        try:
            with pytest.raises(ThymisToolError) as failure:
                await tools.invoke("deploy", {"config_identifiers": ["kiosk"]})
            with pytest.raises(UnknownToolError):
                await tools.invoke("does_not_exist")
            with pytest.raises(ValidationError):
                await tools.invoke("build_project", {"unexpected": True})
            return failure.value
        finally:
            await client.aclose()

    failure = asyncio.run(scenario())
    assert failure.status_code == 409
    assert failure.method == "POST"
    assert failure.path == "/api/action/deploy"
    assert failure.detail == "Repository is dirty. Please commit your changes first."
