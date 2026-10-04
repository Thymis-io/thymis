args@{ ... }:
let
  inherit (args) inputs lib;
  rpi = inputs.nixos-raspberrypi.nixosModules;
  # Boot firmware-native instead of chain-loading u-boot: `kernel` puts
  # kernel.img + initrd on the firmware partition and points config.txt at them,
  # which is the layout these boards have always booted. u-boot + extlinux did
  # not come up on a Pi 4B (the boot never reached userspace).
  #
  # configurationLimit counts *additional* generations on the firmware
  # partition (the default one is always kept), and each costs a kernel +
  # initrd (~64 MiB) plus a temporary copy while it is installed. Devices
  # flashed with the previous raspberry-pi-nix layout only have 128 MiB there,
  # so keep just the default generation; raise it on devices with the 1 GiB
  # partition that new images use.
  #
  # A single generation still has to fit *twice* over: `nixos-generations-builder`
  # writes the new generation to `<firmware>/nixos/default.tmp.$$` and only then
  # swaps it in, keeping the outgoing directory as `.bkp` until the move
  # succeeds. On a 128 MiB partition (a 26.05 Pi 4B: kernel 33.5 MiB, initrd
  # 27 MiB) the incoming kernel + initrd do not fit next to the current ones,
  # so the switch fails — and a failure halfway through writing a FAT boot
  # partition is a card that can't be reimaged. Hence: ship a smaller firmware
  # payload, and check the space *before* anything is written.
  #
  # `pkgs.raspberrypifw` ships `start*.elf` for every board generation plus
  # debug (`*_db`) and cut-down (`*_cd`) builds — 21.5 MiB, a sixth of that
  # partition — and the firmware populate step re-copies all of them on every
  # switch. A card only ever executes one family: BCM2835/6/7 (Pi 1/2/3) boots
  # `start.elf`/`start_x.elf`, BCM2711/2712 (Pi 4/5) boots `start4*.elf`, and
  # the debug/cut-down builds are only used when explicitly renamed.
  firmwareDropFor = board:
    [
      "start_db.elf"
      "start_cd.elf"
      "start4db.elf"
      "start4cd.elf"
    ]
    ++ {
      raspberry-pi-3 = [ "start4.elf" "start4x.elf" ];
      raspberry-pi-4 = [ "start.elf" "start_x.elf" ];
      # BCM2712: which family the Pi 5 firmware picks has not been verified
      # here, so keep both.
      raspberry-pi-5 = [ ];
    }.${board};

  trimmedFirmware = board: pkgs:
    pkgs.runCommand "raspberrypifw-${board}" { } ''
      mkdir -p $out/share/raspberrypi/boot
      cp -r ${pkgs.raspberrypifw}/share/raspberrypi/boot/. $out/share/raspberrypi/boot/
      chmod -R u+w $out
      cd $out/share/raspberrypi/boot
      rm -f ${lib.concatStringsSep " " (firmwareDropFor board)}
      echo "start*.elf kept for ${board}: $(ls start*.elf | tr '\n' ' ')"
    '';

  rpiBootloader = board: { pkgs, lib, ... }: {
    boot.loader.raspberry-pi.bootloader = lib.mkForce "kernel";
    boot.loader.raspberry-pi.configurationLimit = lib.mkDefault 0;
    boot.loader.raspberry-pi.firmwarePackage = trimmedFirmware board pkgs;

    # Staging needs room for the incoming kernel + initrd, so refuse the switch
    # before the bootloader install touches the partition. Runs before
    # `do_install_bootloader` and aborts the switch on non-zero exit.
    system.preSwitchChecks.raspberry-pi-firmware-space = ''
      fw=/boot/firmware
      if [ -d "$fw" ]; then
        kernel=$(stat -c %s "$1/kernel" 2>/dev/null || echo 0)
        initrd=$(stat -c %s "$1/initrd" 2>/dev/null || echo 0)
        need=$((kernel + initrd))
        avail=$(df -B1 --output=avail "$fw" | tail -n 1)
        if [ "$avail" -lt "$need" ]; then
          echo "refusing to switch: $fw cannot hold the new kernel + initrd"
          echo "  need  $((need / 1048576)) MiB free (kernel $((kernel / 1048576)) MiB + initrd $((initrd / 1048576)) MiB)"
          echo "  avail $((avail / 1048576)) MiB"
          echo "Boot files are staged next to the current generation, so the partition needs room for the incoming pair."
          exit 1
        fi
      fi
    '';
  };
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
          (rpiBootloader "raspberry-pi-3")
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
          (rpiBootloader "raspberry-pi-4")
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
          (rpiBootloader "raspberry-pi-5")
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
