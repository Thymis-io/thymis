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
      };
      install-iso = { config, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.install-iso
        ];
        system.build.thymis-image = config.system.build.isoImage;
        warnings = [ "This format is not entirely supported yet" ];
      };
      sd-card-image = { config, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.sd-aarch64
        ];
        sdImage.compressImage = false;
        system.build.thymis-image = config.system.build.sdImage;
      };
    };
in
imageFormats
