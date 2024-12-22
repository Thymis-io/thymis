args@{ ... }:
let
  inherit (args) inputs lib;
  deviceConfig =
    {
      generic-x86_64 = { ... }: {
        nixpkgs.hostPlatform = "x86_64-linux";
      };
      generic-aarch64 = { ... }: {
        nixpkgs.hostPlatform = "aarch64-linux";
      };
      raspberry-pi-3 = { modulesPath, ... }: {
        disabledModules = [
          "${modulesPath}/installer/sd-card/sd-image-aarch64.nix"
        ];
        imports = [
          inputs.raspberry-pi-nix.nixosModules.raspberry-pi
        ];
        raspberry-pi-nix.board = "bcm2711";
        hardware.raspberry-pi.config = {
          all = {
            base-dt-params = {
              audio = {
                enable = true;
              };
            };
          };
        };
        boot.kernelModules = [ "vc4" "bcm2835_dma" "i2c_bcm2835" ];
        nixpkgs.overlays = [
          (final: super: {
            makeModulesClosure = x:
              super.makeModulesClosure (x // { allowMissing = true; });
          })
        ];
        nixpkgs.hostPlatform = "aarch64-linux";
      };
      raspberry-pi-4 = { modulesPath, ... }: {
        disabledModules = [
          "${modulesPath}/installer/sd-card/sd-image-aarch64.nix"
        ];
        imports = [
          inputs.raspberry-pi-nix.nixosModules.raspberry-pi
        ];
        raspberry-pi-nix.board = "bcm2711";
        boot.kernelParams = [ "snd_bcm2835.enable_headphones=1" "snd_bcm2835.enable_hdmi=1" ];
        hardware.raspberry-pi.config = {
          all = {
            dt-overlays = {
              vc4-fkms-v3d = { enable = true; params = { }; };
            };
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
      raspberry-pi-5 = { pkgs, modulesPath, ... }: {
        disabledModules = [
          "${modulesPath}/installer/sd-card/sd-image-aarch64.nix"
        ];
        imports = [
          inputs.raspberry-pi-nix.nixosModules.raspberry-pi
        ];
        raspberry-pi-nix.libcamera-overlay.enable = false;
        raspberry-pi-nix.board = "bcm2712";
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
        hardware.graphics = {
          enable = true;
          extraPackages = [ pkgs.mesa.drivers ];
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
