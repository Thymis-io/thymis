args@{ inputs, lib, ... }:
let
  devices = import ./devices.nix { lib = inputs.nixpkgs.lib; };
  device-names = builtins.attrNames devices;
in
assert lib.assertMsg
  (builtins.elem args.thymis-config.device-type device-names)
  "thymis-config.device-type must be one of ${builtins.toJSON device-names}. Got ${args.thymis-config.device-type}";
(import ./devices.nix args).${args.thymis-config.device-type}
