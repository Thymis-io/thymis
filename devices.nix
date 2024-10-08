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
      raspberry-pi-3 = { ... }: {
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
          inputs.nixos-hardware.nixosModules.raspberry-pi-4
        ];
        hardware.raspberry-pi."4".fkms-3d.enable = true;
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
