# Derives the time zone and NTP server configuration from the settings of the
# Localization module. See `nix/settings/networking.nix` for how the settings
# and their priorities are provided by the controller.
{ config, lib, ... }:
let
  cfg = config.thymis.config.localization or { };
  priorities = config.thymis.priority.localization or { };
  defaultPriority = 1500;
  priority = name: priorities.${name} or defaultPriority;

  timezone = cfg.timezone or "";
  timeServers = cfg.time-servers or [ ];
in
{
  config = {
    time.timeZone = lib.mkIf (timezone != "") (lib.mkOverride
      (priority "timezone")
      timezone);

    # a list option: no `mkOverride`, so that time servers contributed by
    # other modules are kept (the priority already decided which list wins)
    networking.timeServers = lib.mkIf (timeServers != [ ])
      (map (server: server.server or "") timeServers);
  };
}
