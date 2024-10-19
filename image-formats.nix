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
        ];
        sdImage.compressImage = false;
        system.build.thymis-image = config.system.build.sdImage;
        key = "github:thymis-io/thymis/image-formats.nix:sd-card-image";
      };
    };
in
imageFormats
