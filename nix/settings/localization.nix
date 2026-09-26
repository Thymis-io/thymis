# Derives the time zone and NTP server configuration from the settings of the
# Localization module. See `nix/module-settings.nix` for the helpers and
# `nix/settings/networking.nix` for a module with more settings.
{ config, lib, ... }:
let
  settings = import ../module-settings.nix { inherit config lib; };
  timeServers = settings.value "localization" "time-servers" [ ];
in
{
  config = {
    time.timeZone = settings.apply "localization" "timezone" "UTC";

    # a list option: no `mkOverride`, so that time servers contributed by other
    # modules are kept (the priority already decided which list wins)
    networking.timeServers = lib.mkIf (timeServers != [ ])
      (map (server: server.server or "") timeServers);
  };
}
