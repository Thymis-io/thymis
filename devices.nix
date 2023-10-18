{ inputs, modulesPath, ... }:
let sharedConfig = {
  imports = [
    inputs.nixos-generators.nixosModules.all-formats
  ];
};
in
builtins.mapAttrs (name: config: sharedConfig // config)
{
  generic-x86_64 = {
    formatConfigs = lib.mkDefault {
      qcow = { imports = [ inputs.nixos-generators.nixosModules.qcow2 ]; };
      install-iso = { imports = [ inputs.nixos-generators.nixosModules.install-iso ]; };
    };
  };
  generic-aarch64 = {
    qcow = { imports = [ inputs.nixos-generators.nixosModules.qcow2 ]; };
  };
  raspberry-pi-4 = {
    sd-card-image = {
      imports = [
        inputs.nixos-generators.nixosModules.sd-aarch64
        inputs.nixos-hardware.nixosModules.raspberry-pi-4
      ];
    };
  };
  raspberry-pi-zero = {
    sd-card-image = {
      imports = [
        "${modulesPath}/installer/sd-card/sd-image-raspberrypi.nix"
      ];
      formatAttr = "sdImage";
    };
  };
  # rock-pi-4 = {};
}
