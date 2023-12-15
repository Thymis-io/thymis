args@{ ... }:
let
  inherit (args) inputs lib;
  sharedConfig = {
    imports = [
      inputs.nixos-generators.nixosModules.all-formats
    ];
  };
  deviceConfig = builtins.mapAttrs (name: config: lib.attrsets.recursiveUpdate sharedConfig config)
    {
      generic-x86_64 = {
        formatConfigs = lib.mkForce {
          qcow = { imports = [ inputs.nixos-generators.nixosModules.qcow ]; };
          install-iso = {
            imports = [ inputs.nixos-generators.nixosModules.install-iso ];
            isoImage.squashfsCompression = "zstd -Xcompression-level 6";
          };
        };
        nixpkgs.hostPlatform = "x86_64-linux";
      };
      generic-aarch64 = {
        formatConfigs = lib.mkForce {
          qcow = { imports = [ inputs.nixos-generators.nixosModules.qcow ]; };
        };
        nixpkgs.hostPlatform = "aarch64-linux";
      };
      raspberry-pi-4 = {
        imports = [
          inputs.nixos-generators.nixosModules.all-formats
          inputs.nixos-hardware.nixosModules.raspberry-pi-4
          inputs.nixos-generators.nixosModules.sd-aarch64

        ];
        formatConfigs = lib.mkForce {
          sd-card-image = {
            imports = [
              inputs.nixos-generators.nixosModules.sd-aarch64
            ];
            sdImage.compressImage = false;
            fileExtension = ".img";
          };
        };
        nixpkgs.overlays = [
          (final: super: {
            makeModulesClosure = x:
              super.makeModulesClosure (x // { allowMissing = true; });
          })
        ];
        nixpkgs.hostPlatform = "aarch64-linux";
      };
      # raspberry-pi-zero = {
      #   formatConfigs = lib.mkForce {
      #     sd-card-image = {
      #       imports = [
      #         "${inputs.nixpkgs}/nixos/modules/installer/sd-card/sd-image-raspberrypi.nix"
      #       ];
      #       formatAttr = "sdImage";
      #     };
      #   };
      #   nixpkgs.hostPlatform = "armv6l-linux";
      #   nixpkgs.buildPlatform = "x86_64-linux";
      # };
      # rock-pi-4 = {};
    };
in
deviceConfig
