args@{ ... }:
let
  inherit (args) inputs lib;
  imageFormats =
    {
      qcow = { config, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.qcow
        ];
        system.build.thymis-image = config.system.build.qcow;
        key = "github:thymis-io/thymis/image-formats.nix:qcow";
      };
      install-iso = { config, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.install-iso
        ];
        system.build.thymis-image = config.system.build.isoImage;
        warnings = [ "This format is not entirely supported yet" ];
        key = "github:thymis-io/thymis/image-formats.nix:install-iso";
      };
      sd-card-image = { config, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.sd-aarch64
          "${inputs.raspberry-pi-nix}/sd-image/default.nix"
        ];
        sdImage.compressImage = false;
        system.build.thymis-image = config.system.build.sdImage;
        key = "github:thymis-io/thymis/image-formats.nix:sd-card-image";
      };
      nixos-vm = { config, modulesPath, ... }: {
        imports = [
          "${modulesPath}/virtualisation/qemu-vm.nix"
        ];
        system.build.thymis-image = config.system.build.vm;
        key = "github:thymis-io/thymis/image-formats.nix:nixos-vm";
      };
    };
in
imageFormats
