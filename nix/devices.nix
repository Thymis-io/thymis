args@{ ... }:
let
  inherit (args) inputs;
  disableUpstreamSdImage = modulesPath: [
    "${modulesPath}/installer/sd-card/sd-image-aarch64.nix"
  ];
in
{
  generic-x86_64 = { ... }: {
    nixpkgs.hostPlatform = "x86_64-linux";
  };

  generic-aarch64 = { ... }: {
    nixpkgs.hostPlatform = "aarch64-linux";
  };

  raspberry-pi-3 = { modulesPath, ... }: {
    disabledModules = disableUpstreamSdImage modulesPath;
    imports = [
      inputs.nixos-raspberrypi.lib.inject-overlays
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-3.base
    ];

    nixpkgs.hostPlatform = "aarch64-linux";
    systemd.settings.Manager.RuntimeWatchdogSec = "15s";
    boot.kernelModules = [ "vc4" "bcm2835_dma" "i2c_bcm2835" ];
    boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;

    hardware.raspberry-pi.config.all.base-dt-params.audio = {
      enable = true;
      value = "on";
    };
  };

  raspberry-pi-4 = { modulesPath, ... }: {
    disabledModules = disableUpstreamSdImage modulesPath;
    imports = [
      inputs.nixos-raspberrypi.lib.inject-overlays
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-4.base
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-4.display-vc4
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-4.bluetooth
    ];

    nixpkgs.hostPlatform = "aarch64-linux";
    systemd.settings.Manager.RuntimeWatchdogSec = "15s";
    boot.kernelParams = [
      "snd_bcm2835.enable_headphones=1"
      "snd_bcm2835.enable_hdmi=1"
      "brcmfmac.roamoff=1"
      "brcmfmac.feature_disable=0x282000"
    ];
    boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;

    hardware.raspberry-pi.config.all.base-dt-params.audio = {
      enable = true;
      value = "on";
    };
  };

  raspberry-pi-5 = { pkgs, modulesPath, ... }: {
    disabledModules = disableUpstreamSdImage modulesPath;
    imports = [
      inputs.nixos-raspberrypi.lib.inject-overlays
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-5.base
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-5.page-size-16k
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-5.display-vc4
      inputs.nixos-raspberrypi.nixosModules.raspberry-pi-5.bluetooth
    ];

    nixpkgs.hostPlatform = "aarch64-linux";
    boot.loader.raspberry-pi.bootloader = "kernel";
    systemd.settings.Manager.RuntimeWatchdogSec = "15s";
    boot.kernel.sysctl."vm.mmap_rnd_bits" = 24;

    hardware.raspberry-pi.config.all.base-dt-params.audio = {
      enable = true;
      value = "on";
    };

    hardware.graphics = {
      enable = true;
      extraPackages = [ pkgs.mesa ];
    };
  };
}
