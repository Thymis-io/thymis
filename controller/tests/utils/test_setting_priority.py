"""Per-setting priority overrides: a setting can carry its own lib.mkOverride
priority instead of using the priority of the tag/configuration it belongs to."""

import io
import pathlib

from thymis_controller import models
from thymis_controller.lib import HOST_PRIORITY, get_config_device_name
from thymis_controller.modules.kiosk import Kiosk
from thymis_controller.modules.networking import NetworkingModule
from thymis_controller.modules.oci_container import OCIContainers
from thymis_controller.modules.thymis import ThymisDevice

DEFAULT_PRIORITY = 100


def _write(module, settings, priorities=None, priority=DEFAULT_PRIORITY, path=None):
    f = io.StringIO()
    module.write_nix_settings(
        f,
        path or pathlib.Path("/tmp/project/hosts/c1"),
        models.ModuleSettings(
            type=module.type, settings=settings, priorities=priorities or {}
        ),
        priority,
        None,
    )
    return f.getvalue()


def test_setting_without_priorities_keeps_module_priority():
    """The absence of overrides must not change the generated nix."""
    settings = {"wifi_ssid": "mynet", "authorized_keys": [{"key": "ssh-rsa AAA"}]}

    without = _write(NetworkingModule(), {"wifi_ssid": "mynet"})
    assert "thymis.config.wifi-ssid = lib.mkOverride 100" in without

    # an unrelated entry in `priorities` must not leak into other settings
    other = _write(NetworkingModule(), settings, priorities={"nameservers": 70})
    assert "thymis.config.wifi-ssid = lib.mkOverride 100" in other


def test_nix_attr_name_setting_uses_its_own_priority():
    out = _write(
        NetworkingModule(), {"wifi_ssid": "mynet"}, priorities={"wifi_ssid": 70}
    )
    assert "thymis.config.wifi-ssid = lib.mkOverride 70" in out


def test_networking_template_uses_per_setting_priorities():
    out = _write(
        NetworkingModule(),
        {
            "static_networks": [
                {
                    "interface": "ens3",
                    "ipv4address": "10.0.0.2",
                    "ipv4prefixLength": 24,
                    "isDefaultGateway": True,
                    "gateway": "10.0.0.1",
                }
            ],
            "nameservers": [{"nameserver": "1.1.1.1"}],
        },
        priorities={"static_networks": 65, "nameservers": 55},
    )
    assert 'interfaces."ens3" = lib.mkOverride 65' in out
    assert "defaultGateway = lib.mkOverride 65" in out
    assert "nameservers = lib.mkOverride 55" in out


def test_thymis_device_uses_per_setting_priorities():
    out = _write(
        ThymisDevice(),
        {"device_type": "generic-x86_64", "agent_controller_url": "http://c:8000"},
        priorities={"agent_controller_url": 45},
    )
    assert "thymis.config.agent.controller-url = lib.mkOverride 45" in out
    assert "thymis.config.device-type = lib.mkOverride 100" in out

    out = _write(
        ThymisDevice(), {"device_name": "host1"}, priorities={"device_name": 55}
    )
    assert 'thymis.config.device-name = lib.mkOverride 55 "host1"' in out


def test_oci_containers_use_containers_priority(tmp_path):
    module = OCIContainers()
    settings = models.ModuleSettings(
        type=module.type,
        settings={"containers": [{"container_name": "web", "image": "nginx:latest"}]},
        priorities={"containers": 75},
    )
    module.write_nix(tmp_path, settings, DEFAULT_PRIORITY, None)

    out = (tmp_path / f"{module.type}.nix").read_text()
    assert "virtualisation.podman = lib.mkOverride 75" in out
    assert 'virtualisation.oci-containers.containers."web" = lib.mkOverride 75' in out


def test_device_name_resolution_honours_overrides():
    device_module = models.ModuleSettings(
        type="thymis_controller.modules.thymis.ThymisDevice",
        settings={"device_name": "from-config"},
    )
    tag = models.Tag(
        displayName="Tag",
        identifier="tag",
        priority=90,
        modules=[
            models.ModuleSettings(
                type="thymis_controller.modules.thymis.ThymisDevice",
                settings={"device_name": "from-tag"},
            )
        ],
    )
    config = models.Config(
        displayName="Config",
        identifier="config",
        tags=["tag"],
        modules=[device_module],
    )
    state = models.State(configs=[config], tags=[tag])

    # config at HOST_PRIORITY(80) wins over tag(90)
    assert get_config_device_name(config, state) == "from-config"

    # tag beats the config once it is overridden to a lower number
    tag.modules[0].priorities = {"device_name": HOST_PRIORITY - 10}
    assert get_config_device_name(config, state) == "from-tag"

    # and an override on the config wins again
    device_module.priorities = {"device_name": HOST_PRIORITY - 20}
    assert get_config_device_name(config, state) == "from-config"


def test_priority_overridable_capability_is_exposed():
    networking = NetworkingModule()
    assert networking.wifi_ssid.get_model("en").priorityOverridable
    assert networking.static_networks.get_model("en").priorityOverridable

    thymis = ThymisDevice()
    assert thymis.agent_controller_url.get_model("en").priorityOverridable
    assert thymis.device_name.get_model("en").priorityOverridable
    assert OCIContainers().containers.get_model("en").priorityOverridable

    # kiosk embeds all settings in one shared definition: no per-setting priority
    assert not Kiosk().volume.get_model("en").priorityOverridable
