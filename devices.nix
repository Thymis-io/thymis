args@{ ... }:
let
  inherit (args) inputs lib;
  deviceConfig =
    {
      generic-x86_64 = { ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.all-formats
        ];
        formatConfigs = lib.mkForce {
          qcow = { imports = [ inputs.nixos-generators.nixosModules.qcow ]; };
          install-iso = {
            imports = [ inputs.nixos-generators.nixosModules.install-iso ];
            isoImage.squashfsCompression = "zstd -Xcompression-level 6";
          };
        };
        nixpkgs.hostPlatform = "x86_64-linux";
      };
      generic-aarch64 = { ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.all-formats
        ];
        formatConfigs = lib.mkForce {
          qcow = { imports = [ inputs.nixos-generators.nixosModules.qcow ]; };
        };
        nixpkgs.hostPlatform = "aarch64-linux";
      };
      raspberry-pi-3 = { ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.all-formats
          #inputs.nixos-hardware.nixosModules.raspberry-pi-3
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
      raspberry-pi-4 = { ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.all-formats
          inputs.nixos-hardware.nixosModules.raspberry-pi-4
          inputs.nixos-generators.nixosModules.sd-aarch64
        ];
        hardware.raspberry-pi."4".fkms-3d.enable = true;
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
      raspberry-pi-5 = { pkgs, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.all-formats
          inputs.raspberry-pi-nix.nixosModules.raspberry-pi
        ];
        raspberry-pi-nix.libcamera-overlay.enable = false;
        raspberry-pi-nix.board = "bcm2712";
        formatConfigs = lib.mkForce {
          sd-card-image = {
            sdImage.compressImage = false;
            fileExtension = ".img";
            formatAttr = "sdImage";
          };
        };
        nixpkgs.overlays = [
          (final: super: {
            makeModulesClosure = x:
              super.makeModulesClosure (x // { allowMissing = true; });
          })
        ];
        nixpkgs.hostPlatform = "aarch64-linux";
        hardware.raspberry-pi.config = {
          all = {
            dt-overlays = {
              vc4-kms-v3d-pi5 = { enable = true; params = { }; };
            };
          };
        };
        hardware.opengl = {
          enable = true;
          extraPackages = [ pkgs.mesa.drivers ];
          driSupport = true;
        };
        services.xserver.extraConfig = ''
          Section "OutputClass"
            Identifier "vc4"
            MatchDriver "vc4"
            Driver "modesetting"
            Option "PrimaryGPU" "true"
          EndSection
        '';
      };
    };
in
deviceConfig
