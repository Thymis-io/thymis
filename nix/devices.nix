args@{ ... }:
let
  inherit (args) inputs lib;
  rpi = inputs.nixos-raspberrypi.nixosModules;
  deviceConfig =
    {
      generic-x86_64 = { ... }: {
        nixpkgs.hostPlatform = "x86_64-linux";
      };
      generic-aarch64 = { ... }: {
        nixpkgs.hostPlatform = "aarch64-linux";
      };
      # The controller renders its project flake with nixpkgs.lib.nixosSystem and
      # only provides `specialArgs.inputs`, so the modules below must supply both
      # the platform and the nixos-raspberrypi flake reference themselves.
      raspberry-pi-3 = { ... }: {
        imports = [
          rpi.raspberry-pi-3.base
        ];
        _module.args.nixos-raspberrypi = inputs.nixos-raspberrypi;
        nixpkgs.hostPlatform = "aarch64-linux";
        systemd.watchdog.runtimeTime = "15s";
        boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;
      };
      raspberry-pi-4 = { ... }: {
        imports = [
          rpi.raspberry-pi-4.base
          rpi.raspberry-pi-4.display-vc4
        ];
        _module.args.nixos-raspberrypi = inputs.nixos-raspberrypi;
        nixpkgs.hostPlatform = "aarch64-linux";
        systemd.watchdog.runtimeTime = "15s";
        boot.kernelParams = [ "brcmfmac.roamoff=1" "brcmfmac.feature_disable=0x282000" ];
        boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;
      };
      raspberry-pi-5 = { ... }: {
        imports = [
          rpi.raspberry-pi-5.base
          rpi.raspberry-pi-5.display-vc4
        ];
        _module.args.nixos-raspberrypi = inputs.nixos-raspberrypi;
        nixpkgs.hostPlatform = "aarch64-linux";
        systemd.watchdog.runtimeTime = "15s";
        boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;
      };
    };
in
deviceConfig
