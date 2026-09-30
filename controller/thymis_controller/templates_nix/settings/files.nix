# Derives the artifact placement of a device from the settings of the Files
# module.
#
# The settings are merged by the nix module system, this file only translates
# the merged values into NixOS configuration. The merged value already resolves
# which artifacts win and with which priority, so the rule list is only
# contributed: it must not carry a priority, which would replace the
# `systemd.tmpfiles.rules` of the device module and of nixpkgs. See
# `nix/module-settings.nix` for the helpers used here.
#
# The secrets of the same module are not consumed here: they are placed on the
# device by the agent at runtime, so nix only keeps their
# `thymis.config.files` definitions for merging and priority.
{ config, lib, pkgs, inputs, ... }:
let
  settings = import ../module-settings.nix { inherit config lib; };

  # The artifacts are merged by nix as an attribute set keyed by the path they
  # are placed at, so the attribute name is the target path of the rule.
  artifacts = settings.value "files" "artifacts" { };

  # An element without an artifact only carries placement metadata, it produces
  # no rule. Unset metadata renders as the tmpfiles default.
  ruleFor = path: artifact:
    lib.optional ((artifact.artifact or "") != "")
      "C+ ${path} ${artifact.mode or "-"} ${artifact.owner or "-"} ${artifact.group or "-"} - ${pkgs.copyPathToStore (inputs.self + "/artifacts/${artifact.artifact}")}";

  rules = lib.concatLists (lib.mapAttrsToList ruleFor artifacts);
in
{
  # A Files module without artifacts must not define anything.
  systemd.tmpfiles.rules = lib.mkIf (rules != [ ]) rules;
}
