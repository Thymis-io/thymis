# Derives the OCI container configuration of a device from the settings of the
# OCI Containers module.
#
# The settings are merged by the nix module system, so this file only has to
# translate the merged values into NixOS configuration. Every definition it
# writes carries the priority its setting was written with
# (`thymis.priority.oci-containers.<setting>`, see `Module.settings_namespace`),
# so that the device configuration or tag that set the setting keeps winning
# against lower priority sources and against raw custom nix.
{ config, lib, ... }:
let
  cfg = config.thymis.config.oci-containers or { };
  priorities = config.thymis.priority.oci-containers or { };
  defaultPriority = 1500;
  priority = name: priorities.${name} or defaultPriority;

  containers = cfg.containers or { };

  # The module writes the priority of its `containers` setting even when no
  # container is configured, so its presence means "the module instance
  # exists" and every container setting is derived with that priority.
  moduleEnabled = priorities ? containers;
  containerPriority = priority "containers";

  # `environment` and `labels` are lists of `{ key, value }` settings, the
  # NixOS container options take them as attribute sets.
  entryToAttr = entry: {
    name = entry.key;
    value = entry.value;
  };

  entriesToAttrs = entries: lib.listToAttrs (map entryToAttr entries);

  # `volumes` and `ports` are lists of `{ host, container }` settings, the
  # NixOS container options take them as `"<host>:<container>"` strings.
  pairsToStrings = pairs: map (pair: "${pair.host}:${pair.container}") pairs;

  # The container name is the attribute key of the element, it is not part of
  # the merged element itself. The list valued options are written without
  # `mkOverride`: overriding one would drop every definition outside the
  # winning priority group instead of merging with it.
  containerConfig = container: {
    image = lib.mkOverride containerPriority (container.image or "");
    environment = lib.mkIf (container ? environment)
      (lib.mkOverride containerPriority (entriesToAttrs container.environment));
    volumes = lib.mkIf (container ? volumes) (pairsToStrings container.volumes);
    ports = lib.mkIf (container ? ports) (pairsToStrings container.ports);
    labels = lib.mkIf (container ? labels)
      (lib.mkOverride containerPriority (entriesToAttrs container.labels));
    log-driver = lib.mkOverride containerPriority "journald";
  };
in
{
  virtualisation.podman = lib.mkIf moduleEnabled {
    enable = lib.mkOverride containerPriority true;
    autoPrune.enable = lib.mkOverride containerPriority true;
    dockerCompat = lib.mkOverride containerPriority true;
    # Required for container networking to be able to use names.
    defaultNetwork.settings.dns_enabled = lib.mkOverride containerPriority true;
  };

  virtualisation.oci-containers.backend =
    lib.mkIf moduleEnabled (lib.mkOverride containerPriority "podman");

  virtualisation.oci-containers.containers = lib.mkIf (containers != { })
    (lib.mkOverride containerPriority
      (lib.mapAttrs (name: container: containerConfig container) containers));
}
