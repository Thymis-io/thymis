"""Merging of module settings across configurations, tags and custom nix.

Every setting is written as `lib.mkOverride <priority>` definitions under
`thymis.config.<module namespace>`, which the nix module system merges: fields
of one setting coming from different sources merge individually, a field
defined by several sources is resolved by priority, and the settings
translation in `nix/settings/` derives NixOS configuration with the priority of
the setting it comes from.
"""

import pathlib

import pytest
from tests.utils import nix_fixture
from thymis_controller import models
from thymis_controller.lib import HOST_PRIORITY

NETWORKING = "thymis_controller.modules.networking.NetworkingModule"
WHATEVER = "thymis_controller.modules.whatever.WhateverModule"

TAG_PRIORITY = 90


def _networking(settings):
    return models.ModuleSettings(type=NETWORKING, settings=settings)


def _render(tmp_path: pathlib.Path):
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            _networking(
                {
                    "wifi_ssid": "tagnet",
                    "static_networks": [
                        {
                            "interface": "ens3",
                            "ipv4address": "10.0.0.2",
                            "ipv4prefixLength": 24,
                            "isDefaultGateway": True,
                            "gateway": "10.0.0.1",
                        },
                        {
                            "interface": "ens5",
                            "ipv4address": "10.5.0.2",
                            "ipv4prefixLength": 24,
                        },
                    ],
                    "nameservers": [{"nameserver": "9.9.9.9"}],
                }
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[
            _networking(
                {
                    "static_networks": [
                        {
                            "interface": "ens4",
                            "ipv4address": "10.1.0.2",
                            "ipv4prefixLength": 24,
                        },
                        {
                            # field level merge with the tag: the tag sets the IPv4
                            # address of this interface, this configuration adds IPv6
                            "interface": "ens5",
                            "ipv6address": "fd00::2",
                            "ipv6prefixLength": 64,
                        },
                    ],
                    "nameservers": [{"nameserver": "1.1.1.1"}],
                }
            ),
            models.ModuleSettings(
                type=WHATEVER,
                settings={
                    # raw custom nix must lose against the settings of this configuration
                    "settings": 'networking.nameservers = [ "5.5.5.5" ];\nnetworking.timeServers = [ "custom.ntp" ];'
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


def test_networking_fields_and_elements_merge(tmp_path):
    result = _eval(
        tmp_path,
        """
        let cfg = flake.nixosConfigurations.c1.config; in {
          ens3 = cfg.networking.interfaces."ens3".ipv4.addresses;
          ens4 = cfg.networking.interfaces."ens4".ipv4.addresses;
          ens5v4 = cfg.networking.interfaces."ens5".ipv4.addresses;
          ens5v6 = cfg.networking.interfaces."ens5".ipv6.addresses;
          gateway = cfg.networking.defaultGateway;
          nameservers = cfg.networking.nameservers;
          wifi = cfg.thymis.config.wifi-ssid;
          customUntouched = cfg.networking.timeServers;
        }
        """,
    )

    # one element per source, merged by the nix module system
    assert result["ens3"] == [{"address": "10.0.0.2", "prefixLength": 24}]
    assert result["ens4"] == [{"address": "10.1.0.2", "prefixLength": 24}]
    # fields of one element coming from different sources merge
    assert result["ens5v4"] == [{"address": "10.5.0.2", "prefixLength": 24}]
    assert result["ens5v6"] == [{"address": "fd00::2", "prefixLength": 64}]

    # the network marked as default gateway provides the default route
    assert result["gateway"]["address"] == "10.0.0.1"
    assert result["gateway"]["interface"] == "ens3"
    # the configuration's nameservers replace the tag's (the merged setting wins
    # by priority) ...
    assert "1.1.1.1" in result["nameservers"]
    assert "9.9.9.9" not in result["nameservers"]
    # ... and are merged with (not replacing) nameservers custom nix adds, because
    # list options are written without a priority
    assert "5.5.5.5" in result["nameservers"]
    # settings consumed directly by the device module keep working
    assert result["wifi"] == "tagnet"
    # a NixOS option no module setting derives is left to custom nix
    assert result["customUntouched"] == ["custom.ntp"]


def test_defaults_do_not_override_explicit_values_of_other_sources(tmp_path):
    """A source that adds a module without configuring a setting must not
    override the value another source configured explicitly."""
    kiosk = "thymis_controller.modules.kiosk.Kiosk"
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            models.ModuleSettings(
                type=kiosk, settings={"kiosk_url": "https://tag.example"}
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[models.ModuleSettings(type=kiosk, settings={"volume": 90})],
    )
    project = nix_fixture.render_project(tmp_path, tags=[tag], configs=[config])
    out = (project / "hosts" / "c1" / f"{kiosk}.nix").read_text()
    # the URL is not configured by the configuration, so it is only written as a
    # default that loses against the tag's value
    assert "thymis.config.kiosk.url = lib.mkOverride 1500" in out
    assert "thymis.config.kiosk.volume = lib.mkOverride 80 90" in out
    try:
        result = nix_fixture.eval_project(
            project,
            """
            let cfg = flake.nixosConfigurations.c1.config; in {
              url = cfg.thymis.config.kiosk.url;
              i3Config = builtins.readFile cfg.services.xserver.windowManager.i3.configFile;
            }
            """,
        )
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))
    assert result["url"] == "https://tag.example"
    assert "--app='https://tag.example'" in result["i3Config"]


def test_priority_of_derived_configuration_is_the_setting_priority(tmp_path):
    result = _eval(
        tmp_path,
        """
        let options = flake.nixosConfigurations.c1.options; in {
          gatewayPriority = options.networking.defaultGateway.highestPrio;
          nameserversPriority = options.networking.nameservers.highestPrio;
        }
        """,
    )
    # the derived default gateway carries the priority of the `static_networks`
    # setting, i.e. the lowest priority of the sources that set it (the
    # configuration's HOST_PRIORITY), instead of the default priority
    assert result["gatewayPriority"] == HOST_PRIORITY
    # list options are merged by nix and deliberately written without a priority,
    # so that rules of other modules (and of custom nix) are not dropped
    assert result["nameserversPriority"] == 100


def _kiosk_eval(project, extra=""):
    return nix_fixture.eval_project(
        project,
        r"""
let
  cfg = flake.nixosConfigurations.c1.config;
  i3Config = builtins.readFile cfg.services.xserver.windowManager.i3.configFile;
  lines = builtins.filter builtins.isString (builtins.split "\n" i3Config);
  setupLine = builtins.head (builtins.filter
    (l: builtins.match ".*thymis-xrandr-setup.*" l != null) lines);
  xrandrSetup =
    builtins.readFile (builtins.substring 6 (builtins.stringLength setupLine - 7) setupLine);
in {
  inherit i3Config xrandrSetup;
  """
        + extra
        + r"""
}
""",
    )


def test_kiosk_settings_are_merged_and_derived(tmp_path):
    """The kiosk configuration is derived from merged settings, so a tag and a
    configuration can each set different kiosk fields."""
    kiosk = "thymis_controller.modules.kiosk.Kiosk"
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            models.ModuleSettings(
                type=kiosk,
                settings={
                    "kiosk_url": "https://tag.example",
                    "xrandr_mode": "1360x768_60.00",
                    "xrandr_rotation": "left",
                    "volume": 42,
                },
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[
            models.ModuleSettings(
                type=kiosk,
                settings={"volume": 90, "enable_vnc": True, "vnc_password": "secret"},
            )
        ],
    )
    project = nix_fixture.render_project(tmp_path, tags=[tag], configs=[config])
    try:
        result = _kiosk_eval(
            project,
            """
  xserverEnable = cfg.services.xserver.enable;
  autoLoginUser = cfg.services.displayManager.autoLogin.user;
  kioskUser = cfg.users.users.thymiskiosk.isNormalUser;
  pipewire = cfg.services.pipewire.enable;
  pulseaudio = cfg.services.pulseaudio.enable;
  nonce = cfg.systemd.services.display-manager.environment.NONCE;
  activation = cfg.system.activationScripts.restart-display-manager-thymis.text;
  configFilePriority =
    flake.nixosConfigurations.c1.options.services.xserver.windowManager.i3.configFile.highestPrio;""",
        )
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))

    i3 = result["i3Config"]
    # the tag's URL and display mode survive, the configuration does not set them
    assert "--app='https://tag.example'" in i3
    assert "cvt 1360 768 60" in result["xrandrSetup"]
    assert "--rotate left" in result["xrandrSetup"]
    # the configuration's volume wins over the tag's
    assert "--set-volume 90" in i3
    assert "--set-volume 42" not in i3
    # the vnc lines are derived from the configuration's settings
    assert "x0vncserver -display :0" in i3
    assert 'vncpasswd -f <<< \\"secret\\"' in i3

    assert result["xserverEnable"] is True
    assert result["autoLoginUser"] == "thymiskiosk"
    assert result["kioskUser"] is True
    assert result["pipewire"] is False
    assert result["pulseaudio"] is True
    assert len(result["nonce"]) == 64
    assert "display-manager.service" in result["activation"]
    # the derived i3 configuration carries the priority of the setting it comes from
    assert result["configFilePriority"] == HOST_PRIORITY


def test_kiosk_only_writes_vnc_lines_when_enabled(tmp_path):
    kiosk = "thymis_controller.modules.kiosk.Kiosk"
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=[],
        modules=[models.ModuleSettings(type=kiosk, settings={})],
    )
    project = nix_fixture.render_project(tmp_path, configs=[config])
    try:
        result = _kiosk_eval(project)
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))

    i3 = result["i3Config"]
    # the module defaults still configure the kiosk
    assert "--app='https://example.com'" in i3
    assert "--set-volume 100" in i3
    assert "cvt 1920 1080 60" in result["xrandrSetup"]
    assert "--rotate normal" in result["xrandrSetup"]
    # the vnc and audio sink lines are only derived when their setting is set
    assert "x0vncserver" not in i3
    assert "vncpasswd" not in i3
    assert "pactl set-default-sink" not in i3


def test_localization_merges_timezone_and_time_servers(tmp_path):
    """A tag and a configuration can both set the timezone: before the settings
    were merged by nix this failed with a conflicting definition."""
    localization = "thymis_controller.modules.localization.LocalizationModule"
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            models.ModuleSettings(
                type=localization,
                settings={
                    "timezone": "Europe/Berlin",
                    "time_servers": [{"server": "tag.ntp"}],
                },
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[
            models.ModuleSettings(
                type=localization,
                settings={
                    "timezone": "UTC",
                    "time_servers": [{"server": "cfg.ntp"}],
                },
            )
        ],
    )
    project = nix_fixture.render_project(tmp_path, tags=[tag], configs=[config])
    try:
        result = nix_fixture.eval_project(
            project,
            """
            let cfg = flake.nixosConfigurations.c1.config; in {
              timeZone = cfg.time.timeZone;
              timeServers = cfg.networking.timeServers;
              timeZonePriority =
                flake.nixosConfigurations.c1.options.time.timeZone.highestPrio;
            }
            """,
        )
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))

    # the configuration's timezone wins over the tag's, without a conflict
    assert result["timeZone"] == "UTC"
    assert result["timeZonePriority"] == HOST_PRIORITY
    # the time servers are one list setting, so the configuration's list
    # replaces the tag's (the tag's value is not merged into it)
    assert result["timeServers"] == ["cfg.ntp"]


def test_empty_value_clears_the_tag_but_empty_element_fields_do_not(tmp_path):
    """A whole setting the configuration sets to an empty value clears the tag's
    value. Empty fields of a list element are not written, so the fields the tag
    sets for the same element survive."""
    tag = models.Tag(
        displayName="Base",
        identifier="base",
        priority=TAG_PRIORITY,
        modules=[
            _networking(
                {
                    "wifi_ssid": "tagnet",
                    "static_networks": [
                        {
                            "interface": "ens3",
                            "ipv4address": "10.0.0.2",
                            "ipv4prefixLength": 24,
                            "isDefaultGateway": True,
                            "gateway": "10.0.0.1",
                        }
                    ],
                }
            )
        ],
    )
    config = models.Config(
        displayName="c1",
        identifier="c1",
        tags=["base"],
        modules=[
            _networking(
                {
                    # cleared in the configuration: must not keep the tag's SSID
                    "wifi_ssid": "",
                    # the configuration only adds an IPv6 address to the tag's
                    # network, the empty fields are the empty UI template
                    "static_networks": [
                        {
                            "interface": "ens3",
                            "ipv4address": "",
                            "ipv4prefixLength": "",
                            "ipv6address": "fd00::2",
                            "ipv6prefixLength": 64,
                            "isDefaultGateway": "",
                            "gateway": "",
                        }
                    ],
                }
            )
        ],
    )
    project = nix_fixture.render_project(tmp_path, tags=[tag], configs=[config])
    try:
        result = nix_fixture.eval_project(
            project,
            """
            let cfg = flake.nixosConfigurations.c1.config; in {
              wifiSsid = cfg.thymis.config.wifi-ssid;
              ipv4 = cfg.networking.interfaces."ens3".ipv4.addresses;
              ipv6 = cfg.networking.interfaces."ens3".ipv6.addresses;
              gateway = cfg.networking.defaultGateway;
            }
            """,
        )
    except nix_fixture.NixUnavailable as e:
        pytest.skip(str(e))

    assert result["wifiSsid"] == ""
    # the tag's IPv4 address and default gateway survive the configuration's
    # element, which has empty values for those fields
    assert result["ipv4"] == [{"address": "10.0.0.2", "prefixLength": 24}]
    assert result["ipv6"] == [{"address": "fd00::2", "prefixLength": 64}]
    assert result["gateway"]["address"] == "10.0.0.1"
