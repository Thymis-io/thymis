# Derives the OCI container configuration of a device from the settings of the
# OCI Containers module.
#
# The settings are merged by the nix module system, this file only translates
# the merged values into NixOS configuration. See `nix/module-settings.nix` for
# the helpers in `nix/module-settings.nix`.
{ config, lib, ... }:
let
  settings = import ../module-settings.nix { inherit config lib; };

  containers = settings.value "oci-containers" "containers" { };

  # The module writes the priority of its `containers` setting even when no
  # container is configured, so its presence means "the module instance exists".
  moduleEnabled = settings.isSet "oci-containers" "containers";

  # `environment` and `labels` are lists of `{ key, value }` settings, the
  # NixOS container options take them as attribute sets.
  entriesToAttrs = entries:
    lib.listToAttrs (map (entry: { name = entry.key; value = entry.value; }) entries);

  # `volumes` and `ports` are lists of `{ host, container }` settings, the
  # NixOS container options take them as `"<host>:<container>"` strings.
  pairsToStrings = pairs: map (pair: "${pair.host}:${pair.container}") pairs;

  # The container name is the attribute key of the element, it is not part of
  # the merged element itself. The list valued options are written without a
  # priority: a priority on a list option drops the definitions of every other
  # source instead of merging with them.
  containerConfig = container: {
    image = settings.override "oci-containers" "containers" (container.image or "");
    environment = lib.mkIf (container ? environment)
      (settings.override "oci-containers" "containers"
        (entriesToAttrs container.environment));
    volumes = lib.mkIf (container ? volumes) (pairsToStrings container.volumes);
    ports = lib.mkIf (container ? ports) (pairsToStrings container.ports);
    labels = lib.mkIf (container ? labels)
      (settings.override "oci-containers" "containers" (entriesToAttrs container.labels));
    log-driver = settings.override "oci-containers" "containers" "journald";
  };
in
{
  virtualisation.podman = lib.mkIf moduleEnabled {
    enable = settings.override "oci-containers" "containers" true;
    autoPrune.enable = settings.override "oci-containers" "containers" true;
    dockerCompat = settings.override "oci-containers" "containers" true;
    # Required for container networking to be able to use names.
    defaultNetwork.settings.dns_enabled =
      settings.override "oci-containers" "containers" true;
  };

  virtualisation.oci-containers.backend =
    settings.override "oci-containers" "containers" "podman";

  virtualisation.oci-containers.containers = lib.mkIf (containers != { })
    (settings.override "oci-containers" "containers"
      (lib.mapAttrs (name: container: containerConfig container) containers));
}
