import pytest
from thymis_controller.config import global_settings


@pytest.mark.parametrize(
    "agent_access_url, expected",
    [
        ("https://agents.example.com", "https://agents.example.com"),
        (None, "https://ui.example.com"),
    ],
)
def test_agent_access_url_falls_back_to_base_url(
    test_client, monkeypatch, agent_access_url, expected
):
    monkeypatch.setattr(global_settings, "BASE_URL", "https://ui.example.com")
    monkeypatch.setattr(global_settings, "AGENT_ACCESS_URL", agent_access_url)

    response = test_client.get("/api/controller-info")

    assert response.status_code == 200
    assert response.json() == {"agent_access_url": expected}
