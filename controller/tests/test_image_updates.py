import concurrent.futures
import hashlib
import os
import pathlib
import subprocess
from types import SimpleNamespace

import pytest
import thymis_controller.image_updates as image_updates
from thymis_controller.image_updates import (
    config_uses_image_updates,
    next_update_version,
    publish_update_package,
)
from thymis_controller.modules.thymis import ThymisDevice


def _package(path: pathlib.Path, contents: bytes) -> pathlib.Path:
    path.mkdir()
    artifact = path / "thymis_2.nix-store.raw.zst"
    artifact.write_bytes(contents)
    digest = hashlib.sha256(contents).hexdigest()
    (path / "SHA256SUMS").write_text(f"{digest} *{artifact.name}\n", encoding="utf-8")
    return path


def test_publish_update_package_signs_and_replaces(tmp_path):
    first = _package(tmp_path / "first", b"first")
    destination = publish_update_package(first, "display-1", tmp_path)

    assert (destination / "thymis_2.nix-store.raw.zst").read_bytes() == b"first"
    signature = destination / "SHA256SUMS.gpg"
    assert signature.is_file()
    subprocess.run(
        ["gpg", "--batch", "--verify", str(signature), str(destination / "SHA256SUMS")],
        check=True,
        capture_output=True,
        env={
            **os.environ,
            "GNUPGHOME": str(tmp_path / "image-update-signing-keyring"),
        },
    )

    second = _package(tmp_path / "second", b"second")
    replaced = publish_update_package(second, "display-1", tmp_path)
    assert replaced == destination
    assert (replaced / "thymis_2.nix-store.raw.zst").read_bytes() == b"second"
    assert not (tmp_path / "image-updates" / ".display-1.previous").exists()


def test_publish_update_package_keeps_previous_on_exchange_failure(
    tmp_path, monkeypatch
):
    first = _package(tmp_path / "first", b"first")
    second = _package(tmp_path / "second", b"second")
    destination = publish_update_package(first, "display-1", tmp_path)

    def fail_exchange(_first, _second):
        raise OSError("simulated exchange failure")

    monkeypatch.setattr(image_updates, "_exchange_directories", fail_exchange)
    with pytest.raises(OSError, match="simulated exchange failure"):
        publish_update_package(second, "display-1", tmp_path)

    assert (destination / "thymis_2.nix-store.raw.zst").read_bytes() == b"first"


def test_next_update_version_is_monotonic_and_compact():
    assert next_update_version("1785068669.4", 1_785_070_000_000) == "1785070000000"
    assert next_update_version("1785070000000", 1_785_070_000_000) == "1785070000001"


def test_publish_update_package_serializes_same_configuration(tmp_path):
    packages = [
        _package(tmp_path / "concurrent-a", b"a"),
        _package(tmp_path / "concurrent-b", b"b"),
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        destinations = list(
            executor.map(
                lambda package: publish_update_package(
                    package, "concurrent-display", tmp_path
                ),
                packages,
            )
        )

    assert destinations[0] == destinations[1]
    published = destinations[0] / "thymis_2.nix-store.raw.zst"
    assert published.read_bytes() in {b"a", b"b"}
    assert not (tmp_path / "image-updates" / ".concurrent-display.previous").exists()


def test_publish_update_package_rejects_unsafe_configuration_id(tmp_path):
    package = _package(tmp_path / "package", b"payload")

    with pytest.raises(ValueError, match="Unsafe configuration ID"):
        publish_update_package(package, "../outside", tmp_path)


def test_config_uses_image_updates_honors_explicit_and_default_formats():
    image_format_module = ThymisDevice()

    assert config_uses_image_updates(
        [
            (
                image_format_module,
                SimpleNamespace(settings={"image_format": "ab-repart-image"}),
            )
        ]
    )
    assert not config_uses_image_updates(
        [
            (
                image_format_module,
                SimpleNamespace(settings={"device_type": "raspberry-pi-5"}),
            )
        ]
    )
    assert not config_uses_image_updates(
        [
            (
                image_format_module,
                SimpleNamespace(settings={"device_type": "generic-x86_64"}),
            )
        ]
    )
    assert not config_uses_image_updates(
        [
            (
                image_format_module,
                SimpleNamespace(settings={"image_format": "sd-card-image"}),
            )
        ]
    )


def test_new_image_format_does_not_change_legacy_implicit_defaults():
    image_format_module = ThymisDevice()

    assert (
        image_format_module.find_image_format_by_device_type("generic-x86_64")
        == "usb-stick-installer"
    )
    assert (
        image_format_module.find_image_format_by_device_type("raspberry-pi-5")
        == "sd-card-image"
    )
