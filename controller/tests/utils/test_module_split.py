"""Tests for splitting the monolithic ThymisDevice module into separate modules
(Networking, Localization, Security & Access, Files) and the to_0_0_9 migration."""

import io
import pathlib

from thymis_controller import models
from thymis_controller.migration.to_0_0_9 import to_0_0_9
from thymis_controller.modules.files import FilesModule
from thymis_controller.modules.localization import LocalizationModule
from thymis_controller.modules.networking import NetworkingModule
from thymis_controller.modules.security import SecurityAccessModule
from thymis_controller.modules.thymis import ThymisDevice

NETWORKING = "thymis_controller.modules.networking.NetworkingModule"
LOCALIZATION = "thymis_controller.modules.localization.LocalizationModule"
SECURITY = "thymis_controller.modules.security.SecurityAccessModule"
FILES = "thymis_controller.modules.files.FilesModule"
DEVICE = "thymis_controller.modules.thymis.ThymisDevice"


def _modules_by_type(module_list):
    return {m["type"]: m["settings"] for m in module_list}


def test_to_0_0_9_splits_config_settings():
    state = {
        "version": "0.0.8",
        "configs": [
            {
                "displayName": "c1",
                "identifier": "c1",
                "tags": [],
                "modules": [
                    {
                        "type": DEVICE,
                        "settings": {
                            "device_type": "generic-x86_64",
                            "image_format": "nixos-vm",
                            "device_name": "host1",
                            "wifi_ssid": "mynet",
                            "wifi_password": "pw",
                            "timezone": "Europe/Berlin",
                            "password_secret": "abc",
                            "authorized_keys": [{"key": "ssh-rsa AAA"}],
                            "secrets": [{"secret": "s", "path": "/x"}],
                        },
                    }
                ],
            }
        ],
        "tags": [],
    }

    out = to_0_0_9(state)
    assert out["version"] == "0.0.9"

    mods = _modules_by_type(out["configs"][0]["modules"])

    # device-coupled settings stay on ThymisDevice
    assert mods[DEVICE] == {
        "device_type": "generic-x86_64",
        "image_format": "nixos-vm",
        "device_name": "host1",
    }
    assert mods[NETWORKING] == {"wifi_ssid": "mynet", "wifi_password": "pw"}
    assert mods[LOCALIZATION] == {"timezone": "Europe/Berlin"}
    assert mods[SECURITY] == {
        "password_secret": "abc",
        "authorized_keys": [{"key": "ssh-rsa AAA"}],
    }
    assert mods[FILES] == {"secrets": [{"secret": "s", "path": "/x"}]}


def test_to_0_0_9_handles_tags_and_merges_existing_target():
    state = {
        "version": "0.0.8",
        "tags": [
            {
                "displayName": "t",
                "identifier": "t",
                "priority": 0,
                "modules": [
                    {
                        "type": DEVICE,
                        "settings": {"nameservers": [{"nameserver": "1.1.1.1"}]},
                    },
                    # pre-existing target module: migration should merge into it
                    {"type": NETWORKING, "settings": {"wifi_ssid": "tagnet"}},
                ],
            }
        ],
        "configs": [],
    }

    out = to_0_0_9(state)
    mods = _modules_by_type(out["tags"][0]["modules"])
    assert mods[NETWORKING] == {
        "wifi_ssid": "tagnet",
        "nameservers": [{"nameserver": "1.1.1.1"}],
    }
    # only one Networking module entry (merged, not duplicated)
    types = [m["type"] for m in out["tags"][0]["modules"]]
    assert types.count(NETWORKING) == 1


def _write(module, settings):
    f = io.StringIO()
    module.write_nix_settings(
        f,
        pathlib.Path("/tmp/project/hosts/c1"),
        models.ModuleSettings(type=module.type, settings=settings),
        100,
        None,
    )
    return f.getvalue()


def test_networking_writes_static_network_and_wifi():
    out = _write(
        NetworkingModule(),
        {
            "wifi_ssid": "mynet",
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
    )
    assert "networking" in out
    assert "ens3" in out
    assert "10.0.0.2" in out
    assert "1.1.1.1" in out
    assert "thymis.config.wifi-ssid" in out


def test_localization_writes_timezone_and_time_servers():
    out = _write(
        LocalizationModule(),
        {"timezone": "Europe/Berlin", "time_servers": [{"server": "pool.ntp.org"}]},
    )
    assert 'time.timeZone = "Europe/Berlin"' in out
    assert "networking.timeServers" in out
    assert "pool.ntp.org" in out


def test_security_writes_password_keys_and_certs():
    out = _write(
        SecurityAccessModule(),
        {
            "password_secret": "abc",
            "authorized_keys": [{"key": "ssh-rsa AAA"}],
            "security_pki_certificates": [{"certificate": "-----BEGIN CERT-----"}],
        },
    )
    assert "users.users.root.hashedPasswordFile" in out
    assert "users.users.root.openssh.authorizedKeys.keys" in out
    assert "ssh-rsa AAA" in out
    assert "security.pki.certificates" in out


def test_files_writes_artifact_tmpfiles():
    out = _write(
        FilesModule(),
        {
            "artifacts": [{"artifact": "app.bin", "path": "/opt/app", "mode": "0755"}],
        },
    )
    assert "systemd.tmpfiles.rules" in out
    assert "/opt/app" in out
    assert "app.bin" in out


def test_files_register_secret_settings_uses_per_secret_metadata():
    module = FilesModule()
    settings = models.ModuleSettings(
        type=module.type,
        settings={
            "secrets": [
                {
                    "secret": "deadbeef",
                    "path": "/run/secret",
                    "owner": "root",
                    "group": "root",
                    "mode": "0400",
                }
            ]
        },
    )
    registered = module.register_secret_settings(settings, None)
    # the custom (path/owner/group/mode-carrying) entry must be present
    assert any(
        st.on_device_path == "/run/secret"
        and st.on_device_mode == "0400"
        and value == "deadbeef"
        for st, value in registered
    )


def test_device_module_keeps_core_settings_and_writes_imports():
    device = ThymisDevice()
    model = device.get_model("en")
    assert set(model.settings.keys()) == {
        "device_type",
        "image_format",
        "device_name",
        "nix_state_version",
        "agent_controller_url",
    }
    out = _write(device, {"device_type": "generic-x86_64", "image_format": "nixos-vm"})
    assert "imports = [" in out
    assert "thymis-device-generic-x86_64" in out
    assert "thymis-image-nixos-vm" in out
