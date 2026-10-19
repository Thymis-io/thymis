import thymis_controller.modules.modules as module_lib
from thymis_controller.models.state import Config, ModuleSettings, State
from thymis_controller.routers.api_state import invalid_setting_errors

DEVICE_MODULE = "thymis_controller.modules.thymis.ThymisDevice"


def _state_with_controller_url(value):
    return State(
        configs=[
            Config(
                displayName="Device",
                identifier="device",
                tags=[],
                modules=[
                    ModuleSettings(
                        type=DEVICE_MODULE,
                        settings={"agent_controller_url": value},
                    )
                ],
            )
        ]
    )


def test_validate_url_accepts_absolute_http_urls():
    for value in (
        "https://thymis.example.com",
        "http://localhost:8000",
        "https://example.com/base/path?query=1",
        "http://[::1]:8080",
        "",
    ):
        assert module_lib.validate_url(value) is None


def test_validate_url_rejects_non_urls():
    for value in (
        "example.com",
        "ftp://example.com",
        "https://",
        "https://example.com:99999",
        "https://exa mple.com",
        42,
    ):
        assert module_lib.validate_url(value) is not None


def test_invalid_setting_errors_reports_bad_controller_url():
    errors = invalid_setting_errors(_state_with_controller_url("not-a-url"))

    assert len(errors) == 1
    assert "config 'device'" in errors[0]
    assert "agent_controller_url" in errors[0]
    assert "absolute http:// or https://" in errors[0]


def test_invalid_setting_errors_allows_valid_and_empty_controller_urls():
    assert (
        invalid_setting_errors(_state_with_controller_url("https://controller.example"))
        == []
    )
    assert invalid_setting_errors(_state_with_controller_url("")) == []
