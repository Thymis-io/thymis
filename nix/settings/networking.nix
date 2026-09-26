# Derives the networking configuration of a device from the settings of the
# Networking module.
#
# The settings are merged by the nix module system, so this file only has to
# translate the merged values into NixOS configuration. Every definition it
# writes carries the priority its setting was written with
# (`thymis.priority.networking.<setting>`, see `Module.settings_namespace`), so
# that the device configuration or tag that set the setting keeps winning
# against lower priority sources and against raw custom nix.
{ config, lib, ... }:
let
  cfg = config.thymis.config.networking or { };
  priorities = config.thymis.priority.networking or { };
  defaultPriority = 1500;
  priority = name: priorities.${name} or defaultPriority;

  networks = cfg.static-networks or { };
  nameservers = cfg.nameservers or [ ];

  # The network that carries the default route. Keyed elements are merged by
  # nix, so the network is looked up by its `isDefaultGateway` field instead of
  # by position.
  gatewayEntry = lib.findFirst
    (entry: entry.net.isDefaultGateway or false)
    null
    (lib.mapAttrsToList (name: net: { interface = name; inherit net; }) networks);

  hasAddress = net: field: (net.${field} or "") != "";

  # `ipv4.addresses` is a list option: writing it without a priority merges it
  # with addresses other modules add to the same interface.
  # the prefix length is a number setting, but state files also contain it as a string
  toPrefixLength = prefixValue:
    if builtins.isInt prefixValue then prefixValue else lib.toInt prefixValue;

  addresses = addressValue: prefixValue:
    lib.mkIf (addressValue != "") [
      {
        address = addressValue;
        prefixLength = toPrefixLength prefixValue;
      }
    ];
in
{
  config.networking = {
    interfaces = lib.mapAttrs
      (name: net: {
        ipv4.addresses = addresses (net.ipv4address or "") (net.ipv4prefixLength or "");
        ipv6.addresses = addresses (net.ipv6address or "") (net.ipv6prefixLength or "");
      })
      networks;

    defaultGateway = lib.mkIf
      (gatewayEntry != null && hasAddress gatewayEntry.net "ipv4address")
      (lib.mkOverride (priority "static_networks") {
        address = gatewayEntry.net.gateway;
        interface = gatewayEntry.interface;
      });

    defaultGateway6 = lib.mkIf
      (gatewayEntry != null && hasAddress gatewayEntry.net "ipv6address")
      (lib.mkOverride (priority "static_networks") {
        address = gatewayEntry.net.gateway6;
        interface = gatewayEntry.interface;
      });

    # a list option as well: the priority was already applied when the
    # settings were merged, deriving it with a priority would replace
    # nameservers contributed by other modules
    nameservers = lib.mkIf (nameservers != [ ])
      (map (nameserver: nameserver.nameserver or "") nameservers);
  };
}
