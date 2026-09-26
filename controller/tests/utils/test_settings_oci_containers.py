"""Merging of the OCI Containers module settings across configurations, tags and custom nix.

The containers setting is written as `thymis.config.oci-containers.containers`
definitions keyed by the container name, which the nix module system merges:
fields of one container coming from different sources merge individually and
containers of different sources end up next to each other.
`nix/settings/oci-containers.nix` derives the NixOS container configuration
from the merged settings with the priority the setting was written with, so the
device configuration or tag that set the setting keeps winning against raw
custom nix.
"""

import pathlib

import pytest
from tests.utils import nix_fixture
from thymis_controller import models
from thymis_controller.lib import HOST_PRIORITY

OCI_CONTAINERS = "thymis_controller.modules.oci_container.OCIContainers"
WHATEVER = "thymis_controller.modules.whatever.WhateverModule"

TAG_PRIORITY = 90


def _oci_containers(containers):
    return models.ModuleSettings(
        type=OCI_CONTAINERS, settings={"containers": containers}
    )


def _render(tmp_path: pathlib.Path):
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            _oci_containers(
                [
                    {
                        "container_name": "web",
                        "image": "docker.io/library/nginx",
                        "ports": [{"host": "8080", "container": "80"}],
                    }
                ]
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[
            _oci_containers(
                [
                    {
                        # field level merge with the tag: the tag sets the image
                        # and the ports of this container, this configuration
                        # adds the environment and the volumes
                        "container_name": "web",
                        "environment": [{"key": "FOO", "value": "bar"}],
                        "volumes": [{"host": "/srv/web", "container": "/data"}],
                    },
                    {
                        # the tag does not have this container at all
                        "container_name": "db",
                        "image": "docker.io/library/postgres",
                        "labels": [{"key": "app", "value": "db"}],
                    },
                ]
            ),
            models.ModuleSettings(
                type=WHATEVER,
                settings={
                    # raw custom nix must lose against the derived configuration
                    "settings": 'virtualisation.oci-containers.containers."web".image = "custom-image";'
                },
            ),
        ],
    )
    return nix_fixture.render_project(tmp_path, tags=[tag], configs=[config])


def _eval(tmp_path: pathlib.Path, expression: str):
    try:
        return nix_fixture.eval_project(_render(tmp_path), expression)
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))


def test_oci_container_fields_and_elements_merge(tmp_path):
    result = _eval(
        tmp_path,
        """
        let
          containers = flake.nixosConfigurations.c1.config.virtualisation.oci-containers.containers;
        in {
          names = builtins.attrNames containers;
          web = {
            image = containers."web".image;
            environment = containers."web".environment;
            volumes = containers."web".volumes;
            ports = containers."web".ports;
            labels = containers."web".labels;
            logDriver = containers."web".log-driver;
          };
          db = {
            image = containers."db".image;
            environment = containers."db".environment;
            ports = containers."db".ports;
            labels = containers."db".labels;
            logDriver = containers."db".log-driver;
          };
        }
        """,
    )

    # one element per source: the tag's container and the configuration only one
    assert result["names"] == ["db", "web"]

    # fields of one container coming from different sources merge
    assert result["web"]["image"] == "docker.io/library/nginx"
    assert result["web"]["ports"] == ["8080:80"]
    assert result["web"]["environment"] == {"FOO": "bar"}
    assert result["web"]["volumes"] == ["/srv/web:/data"]
    # unset fields keep the NixOS defaults
    assert result["web"]["labels"] == {}
    assert result["web"]["logDriver"] == "journald"

    assert result["db"]["image"] == "docker.io/library/postgres"
    assert result["db"]["labels"] == {"app": "db"}
    assert result["db"]["environment"] == {}
    assert result["db"]["ports"] == []
    assert result["db"]["logDriver"] == "journald"


def test_podman_is_configured_while_the_module_exists(tmp_path):
    result = _eval(
        tmp_path,
        """
        let
          cfg = flake.nixosConfigurations.c1.config;
          podman = cfg.virtualisation.podman;
        in {
          enable = podman.enable;
          autoPrune = podman.autoPrune.enable;
          dockerCompat = podman.dockerCompat;
          dnsEnabled = podman.defaultNetwork.settings.dns_enabled;
          backend = cfg.virtualisation.oci-containers.backend;
        }
        """,
    )

    assert result["enable"] is True
    assert result["autoPrune"] is True
    assert result["dockerCompat"] is True
    assert result["dnsEnabled"] is True
    assert result["backend"] == "podman"


def test_priority_of_derived_configuration_is_the_setting_priority(tmp_path):
    result = _eval(
        tmp_path,
        """
        let
          options = flake.nixosConfigurations.c1.options;
        in {
          containersPriority = options.virtualisation.oci-containers.containers.highestPrio;
          podmanPriority = options.virtualisation.podman.enable.highestPrio;
        }
        """,
    )

    # the configuration sets the containers, so the derived definitions carry
    # its priority (HOST_PRIORITY), not the priority of the tag
    assert result["containersPriority"] == HOST_PRIORITY
    assert result["podmanPriority"] == HOST_PRIORITY
