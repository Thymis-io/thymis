args@{ ... }:
let
  inherit (args) inputs lib;
  rpi = inputs.nixos-raspberrypi.nixosModules;
  # raspberry-pi-nix kept kernel.img/initrd on the firmware partition and passed
  # init=/sbin/init through cmdline.txt. The Raspberry Pi firmware still reads
  # those files, so an in-place upgrade has to remove them or they shadow the
  # u-boot/extlinux boot path that nixos-raspberrypi installs. The path is
  # automounted, and `rm -f` is a no-op when it is not.
  legacyFirmwareCleanup = ''
    for f in cmdline.txt kernel.img initrd; do
      rm -f "/boot/firmware/$f"
    done
  '';
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
          inputs.nixos-raspberrypi.lib.inject-overlays
          inputs.nixos-raspberrypi.nixosModules.trusted-nix-caches
        ];
        _module.args.nixos-raspberrypi = inputs.nixos-raspberrypi;
        nixpkgs.hostPlatform = "aarch64-linux";
        system.activationScripts.raspberry-pi-legacy-firmware = legacyFirmwareCleanup;
        systemd.watchdog.runtimeTime = "15s";
        boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;
      };
      raspberry-pi-4 = { ... }: {
        imports = [
          rpi.raspberry-pi-4.base
          rpi.raspberry-pi-4.display-vc4
          inputs.nixos-raspberrypi.lib.inject-overlays
          inputs.nixos-raspberrypi.nixosModules.trusted-nix-caches
        ];
        _module.args.nixos-raspberrypi = inputs.nixos-raspberrypi;
        nixpkgs.hostPlatform = "aarch64-linux";
        system.activationScripts.raspberry-pi-legacy-firmware = legacyFirmwareCleanup;
        systemd.watchdog.runtimeTime = "15s";
        boot.kernelParams = [ "brcmfmac.roamoff=1" "brcmfmac.feature_disable=0x282000" ];
        boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;
      };
      raspberry-pi-5 = { ... }: {
        imports = [
          rpi.raspberry-pi-5.base
          rpi.raspberry-pi-5.display-vc4
          inputs.nixos-raspberrypi.lib.inject-overlays
          inputs.nixos-raspberrypi.nixosModules.trusted-nix-caches
        ];
        _module.args.nixos-raspberrypi = inputs.nixos-raspberrypi;
        nixpkgs.hostPlatform = "aarch64-linux";
        system.activationScripts.raspberry-pi-legacy-firmware = legacyFirmwareCleanup;
        systemd.watchdog.runtimeTime = "15s";
        boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;
      };
    };
in
deviceConfig
