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
            "list_hardware_devices",
            "get_device_connection_history",
            "get_device_metrics",
            "get_device_error_logs",
            "run_device_command",
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


def test_live_device_tools_map_metrics_and_commands_to_api():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"task_id": "task-1"}, request=request)

    async def scenario():
        tools, client = make_tools(handler)
        try:
            deployment_info_id = "69e2a620-7534-442c-a8a8-2b1eb8d9be87"
            assert await tools.invoke(
                "get_device_metrics",
                {
                    "deployment_info_id": deployment_info_id,
                    "hours": 6,
                    "granularity": "15min",
                },
            ) == {"task_id": "task-1"}
            assert await tools.invoke(
                "run_device_command",
                {
                    "deployment_info_id": deployment_info_id,
                    "command": "systemctl status nginx --no-pager",
                },
            ) == {"task_id": "task-1"}
        finally:
            await client.aclose()

    asyncio.run(scenario())

    metrics_request, command_request = requests
    assert metrics_request.url.path == (
        "/api/deployment_info/69e2a620-7534-442c-a8a8-2b1eb8d9be87/metrics"
    )
    assert str(metrics_request.url.params) == "hours=6&granularity=15min"
    assert command_request.method == "POST"
    assert command_request.url.path == "/api/action/run-command"
    assert (
        command_request.url.params.get("command") == "systemctl status nginx --no-pager"
    )


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


def test_configuration_and_repository_observability_tools_map_to_api():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True}, request=request)

    async def scenario():
        tools, client = make_tools(handler)
        try:
            assert await tools.invoke(
                "get_configuration", {"config_identifier": "kiosk"}
            ) == {"ok": True}
            assert await tools.invoke(
                "patch_configuration_field",
                {
                    "config_identifier": "kiosk",
                    "patch": {
                        "operation": "set",
                        "path": "/modules/0/settings/url",
                        "value": "https://example.test/display",
                    },
                },
            ) == {"ok": True}
            assert await tools.invoke(
                "check_external_repository_api_access",
                {
                    "flake_url": "github:Thymis-io/thymis#main",
                    "api_key_secret": "69e2a620-7534-442c-a8a8-2b1eb8d9be87",
                },
            ) == {"ok": True}
        finally:
            await client.aclose()

    asyncio.run(scenario())

    get_request, patch_request, probe_request = requests
    assert get_request.url.path == "/api/configs/kiosk"
    assert patch_request.url.path == "/api/configs/kiosk/field"
    assert json.loads(patch_request.content) == {
        "operation": "set",
        "path": "/modules/0/settings/url",
        "value": "https://example.test/display",
    }
    assert (
        probe_request.url.params["api_key_secret"]
        == "69e2a620-7534-442c-a8a8-2b1eb8d9be87"
    )
    assert b"github%3AThymis-io%2Fthymis%23main" in probe_request.url.raw_path
