# Helpers for Thymis modules that translate their settings into NixOS
# configuration.
#
# The controller writes every setting of a module instance as
# `lib.mkOverride <priority>` definitions of a settings value
# (`thymis.config.<namespace>.<setting>`), so the nix module system merges the
# settings of a device configuration, its tags and custom nix, and a setting a
# source does not configure is written with the module default and a
# `lib.mkOptionDefault` priority.
#
# A module derives its NixOS configuration from the merged settings and uses
# these helpers to read them and to write the result with the priority of the
# setting it comes from, so that the device configuration or tag that set the
# setting keeps winning over lower priority sources. A module imports them from
# the project it is generated into (the controller copies this file and the
# derivation of every used module into the `modules` directory of the project,
# so that a project keeps building with any version of the thymis flake):
#
#     { config, lib, ... }:
#     let
#       settings = import ../../modules/module-settings.nix { inherit config lib; };
#     in
#     {
#       systemd.services.mymodule.environment.URL =
#         settings.override "mymodule" "url" "https://fallback";
#     }
#
# `namespace` is the `settings_namespace` of the module and `name` is the name
# the setting has in `thymis.config.<namespace>` (the last component of the
# setting's `nix_attr_name`, e.g. `time-servers`). The priorities are written to
# `thymis.config._priority.<namespace>.<name>`.
#
# Note that a list option that several modules contribute to
# (`systemd.tmpfiles.rules`, firewall ports, authorized keys, ...) must be
# written *without* a priority: a priority on a list option drops the
# definitions of all other sources instead of merging with them. Use
# `settings.value` for those.
{ config, lib }:
rec {
  # All merged settings of a module namespace, `{ }` when the module is unused.
  settings = namespace: config.thymis.config.${namespace} or { };

  # The merged value of one setting, or `fallback` when no source set it.
  value = namespace: name: fallback: (settings namespace).${name} or fallback;

  # Whether any source set the setting.
  isSet = namespace: name: (config.thymis.config._priority.${namespace} or { }) ? ${name};

  # The priority the setting was written with (1500 when no source set it).
  priority = namespace: name:
    (config.thymis.config._priority.${namespace} or { }).${name} or 1500;

  # The names of all settings of the namespace that a source published.
  usedSettings = namespace: lib.attrNames (config.thymis.config._priority.${namespace} or { });

  # Whether any source uses the module, i.e. added an instance of it.
  used = namespace: usedSettings namespace != [ ];

  # The lowest priority of the given settings, for configuration derived from
  # several settings at once.
  priorityOf = namespace: names:
    lib.foldl'
      (lowest: name: let p = priority namespace name; in if p < lowest then p else lowest)
      1500
      names;

  # The lowest priority of all settings of the namespace, for configuration
  # derived from the module as a whole.
  lowestPriority = namespace: priorityOf namespace (usedSettings namespace);

  # The setting's own value, wrapped for writing it to a NixOS option of the
  # same meaning (e.g. `time.timeZone = settings.apply "localization" "timezone";`).
  apply = namespace: name: fallback:
    lib.mkIf (isSet namespace name)
      (lib.mkOverride (priority namespace name) (value namespace name fallback));

  # `value` wrapped so that it is only defined when the setting is set and with
  # the priority of the setting.
  override = namespace: name: value:
    lib.mkIf (isSet namespace name) (lib.mkOverride (priority namespace name) value);

  # `value` for configuration derived from several settings: defined when any of
  # them is set, with the lowest of their priorities.
  overrideOf = namespace: names: value:
    lib.mkIf (lib.any (isSet namespace) names) (lib.mkOverride (priorityOf namespace names) value);
}
