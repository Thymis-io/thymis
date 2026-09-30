# Derives the networking configuration of a device from the settings of the
# Networking module.
#
# The settings are merged by the nix module system, this file only translates
# the merged values into NixOS configuration. See `nix/module-settings.nix` for
# the helpers in `nix/module-settings.nix`.
{ config, lib, ... }:
let
  settings = import ../module-settings.nix { inherit config lib; };

  networks = settings.value "networking" "static-networks" { };
  nameservers = settings.value "networking" "nameservers" [ ];

  # The network that carries the default route. Keyed elements are merged by
  # nix, so the network is looked up by its `isDefaultGateway` field instead of
  # by position.
  gatewayEntry = lib.findFirst
    (entry: entry.net.isDefaultGateway or false)
    null
    (lib.mapAttrsToList (name: net: { interface = name; inherit net; }) networks);

  hasAddress = net: field: (net.${field} or "") != "";

  # the prefix length is a number setting, but state files also contain it as a string
  toPrefixLength = prefixValue:
    if builtins.isInt prefixValue then prefixValue else lib.toInt prefixValue;

  # `ipv4.addresses` is a list option: writing it without a priority merges it
  # with addresses other modules add to the same interface.
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
      (settings.override "networking" "static-networks" {
        address = gatewayEntry.net.gateway;
        interface = gatewayEntry.interface;
      });

    defaultGateway6 = lib.mkIf
      (gatewayEntry != null && hasAddress gatewayEntry.net "ipv6address")
      (settings.override "networking" "static-networks" {
        address = gatewayEntry.net.gateway6;
        interface = gatewayEntry.interface;
      });

    # a list option as well: the priority was already applied when the settings
    # were merged, deriving it with a priority would replace nameservers
    # contributed by other modules
    nameservers = lib.mkIf (nameservers != [ ])
      (map (nameserver: nameserver.nameserver or "") nameservers);
  };
}
