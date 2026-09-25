args@{ ... }:
let
  inherit (args) inputs lib;
  image-with-secrets-builder = { pkgs, image-path, start-vm ? "" }: pkgs.callPackage
    ({}: pkgs.writeShellScript "fill-image-with-secrets" ''
      #! ${pkgs.runtimeShell}
      set -euo pipefail
      # set -x

      if [ -z "''${2:-}" ]; then
        echo "Usage: $0 <secret_dir> <final_image_destination_base>"
        exit 1
      fi

      image_dir=${image-path}
      start_vm=${start-vm}
      secret_dir="$1"
      final_image_destination_base="$2"

      secrets_dir_abs=$(realpath "$secret_dir")

      if [ ! -d "$secret_dir" ]; then
        echo "Secret directory does not exist: $secret_dir"
        exit 1
      fi

      if [ ! -d "$image_dir" ]; then
        echo "Image directory does not exist: $image_dir"
        exit 1
      fi

      IMAGE_ENDINGS="qcow2 img iso -vm"
      for ENDING in $IMAGE_ENDINGS; do
        IMAGE_WITH_ENDING=$(find "$image_dir" -name "*$ENDING" -mindepth 1 -type f | head -n 1)
        if ! [ -z "$IMAGE_WITH_ENDING" ]; then
          IMAGE="$IMAGE_WITH_ENDING"
          EXTENSION="$ENDING"
        fi
      done

      if [ -z "''${IMAGE:-}" ]; then
        echo "No image found in $image_dir"
        exit 1
      fi

      FINAL_IMAGE_DESTINATION=$final_image_destination_base.$EXTENSION

      TMPDIR=$(mktemp -d)
      trap 'rm -rf "$TMPDIR"' EXIT

      IS_QCOW2=0
      if ! ${pkgs.file}/bin/file "$IMAGE" | grep -q -e "DOS/MBR boot sector"; then
        if ! ${pkgs.file}/bin/file "$IMAGE" | grep -q -e "QEMU QCOW Image"; then
          ${pkgs.file}/bin/file "$IMAGE"
          echo "Image is not a bootable image"
          exit 1
        fi
        # If it's a qcow2 image, convert it to a raw image, and convert it back to qcow2 later
        RAW_IMAGE="$TMPDIR/image.raw"
        ${pkgs.qemu}/bin/qemu-img convert -f qcow2 -O raw "$IMAGE" "$RAW_IMAGE"
        QCOW_ORIGINAL_IMAGE="$IMAGE"
        IMAGE="$RAW_IMAGE"
        QCOW_ORIGINAL_FINAL_DESTINATION="$FINAL_IMAGE_DESTINATION"
        TMP_RAW_FINAL_IMAGE_DESTINATION="$TMPDIR/image.raw.final_tmp"
        FINAL_IMAGE_DESTINATION="$TMP_RAW_FINAL_IMAGE_DESTINATION"
        IS_QCOW2=1
      fi

      echo "Image: $IMAGE"

      # if EXTENSION is not iso
      if [ "$EXTENSION" != "iso" ]; then
      cp --no-preserve=mode,ownership "$IMAGE" "$FINAL_IMAGE_DESTINATION"

      # if qcow, delete $IMAGE
      if [ $IS_QCOW2 -eq 1 ]; then
        rm -f "$IMAGE"
      fi

      echo "Final image: $FINAL_IMAGE_DESTINATION"
      PARTED_OUTPUT=$(${pkgs.parted}/bin/parted --json -s "$FINAL_IMAGE_DESTINATION" print)
      echo "Parted output: $PARTED_OUTPUT"
      FIRST_FAT_PARTITION_IDX=$(echo "$PARTED_OUTPUT" | ${pkgs.jq}/bin/jq -r '.disk.partitions[] | select((.filesystem // "") | startswith("fat")) | .number' | head -n 1)
      echo "First FAT partition index: $FIRST_FAT_PARTITION_IDX"
      eval "$(${pkgs.util-linux}/bin/partx "$FINAL_IMAGE_DESTINATION" -o START,SECTORS --nr "$FIRST_FAT_PARTITION_IDX" --pairs)"
      echo "First FAT partition starts at $START and has $SECTORS sectors"
      FIRST_FAT_PARTITION_START=$START
      FIRST_FAT_PARTITION_SECTORS=$SECTORS


      echo "Extracting first FAT partition to $TMPDIR/image_first_fat_partition"

      # dd if="$1" of="$2" conv=notrunc skip="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS"
      dd if="$FINAL_IMAGE_DESTINATION" of="$TMPDIR/image_first_fat_partition" conv=notrunc skip="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS"

      echo "Extracted first FAT partition to $TMPDIR/image_first_fat_partition"


      echo "Checking FAT partition"

      ${pkgs.util-linux}/bin/setsid ${pkgs.dosfstools}/bin/fsck.vfat -vn "$TMPDIR/image_first_fat_partition"

      echo "Copying secrets to FAT partition"

      (cd "$secrets_dir_abs" && (${pkgs.util-linux}/bin/setsid ${pkgs.mtools}/bin/mcopy -psvm -i "$TMPDIR/image_first_fat_partition" ./* ::) </dev/null) || (echo "mcopy failed, most probably due to file name conflicts"; exit 1)

      echo "Copying secrets to FAT partition done"

      ${pkgs.util-linux}/bin/setsid ${pkgs.dosfstools}/bin/fsck.vfat -vn "$TMPDIR/image_first_fat_partition"

      echo "Copying back first FAT partition to $FINAL_IMAGE_DESTINATION"

      dd if="$TMPDIR/image_first_fat_partition" of="$FINAL_IMAGE_DESTINATION" conv=notrunc seek="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS" status=progress

      if [ $IS_QCOW2 -eq 1 ]; then
        echo "Converting back to qcow2"
        ${pkgs.qemu}/bin/qemu-img convert -f raw -O qcow2 "$FINAL_IMAGE_DESTINATION" "$QCOW_ORIGINAL_FINAL_DESTINATION"
        rm -f "$FINAL_IMAGE_DESTINATION"
        FINAL_IMAGE_DESTINATION="$QCOW_ORIGINAL_FINAL_DESTINATION"
      fi

      else

      # now use xorriso to add the files to the iso, and copy the result to the final destination at the same time
      (cd "$secrets_dir_abs" && ${pkgs.xorriso}/bin/xorriso -boot_image "any" "keep" -indev "$IMAGE" -outdev "$FINAL_IMAGE_DESTINATION" -add ./*)
      fi

      echo "Final image: $FINAL_IMAGE_DESTINATION"

      if [ -n "$start_vm" ]; then
        START_VM_SCRIPT="$TMPDIR/start-vm"

        # insert "-b $FINAL_IMAGE_DESTINATION" to replace previous "-b whatever/nixos.qcow2"
        sed -e "s@-b .*nixos.qcow2@-b \"$FINAL_IMAGE_DESTINATION\"@" "$start_vm" > "$START_VM_SCRIPT"

        cp "$START_VM_SCRIPT" "$final_image_destination_base.start-vm"

        chmod +x "$final_image_destination_base.start-vm"
        echo "Start VM script: $final_image_destination_base.start-vm"
      fi

      # clean tmpdir
      rm -rf "$TMPDIR"

      echo "Done"
      exit 0
    '')
    { };
  imageFormats =
    {
      qcow = { config, pkgs, ... }: {
        imports = [
          inputs.nixos-generators.nixosModules.qcow
        ];
        # system.build.thymis-image = config.system.build.qcow;
        system.build.thymis-image-with-secrets-builder = image-with-secrets-builder {
          inherit pkgs;
          image-path = config.system.build.qcow;
        };
        system.build.thymis-image-with-secrets-builder-aarch64 = config.system.build.thymis-image-with-secrets-builder;
        system.build.thymis-image-with-secrets-builder-x86_64 = config.system.build.thymis-image-with-secrets-builder;
        key = "github:thymis-io/thymis/image-formats.nix:qcow";
      };
      sd-card-image = { extendModules, ... }:
        {
          imports = [
            inputs.nixos-raspberrypi.nixosModules.sd-image
          ];
          sdImage.compressImage = false;
          # The `kernel` bootloader keeps a kernel + initrd on the firmware
          # partition per generation, so it needs room: pin 1 GiB instead of
          # relying on the upstream default. Devices flashed with the previous
          # raspberry-pi-nix layout only have 128 MiB there, which is why the
          # deploy clears their legacy kernel.img/initrd before switching.
          sdImage.firmwareSize = 1024;
          system.build.thymis-image-with-secrets-builder-aarch64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.aarch64-linux;
            image-path = (extendModules {
              modules = [
                ({ ... }: {
                  users.users.root.openssh.authorizedKeys.keys = lib.mkForce [ ];
                })
              ];
            }).config.system.build.sdImage;
          };
          system.build.thymis-image-with-secrets-builder-x86_64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.x86_64-linux;
            image-path = (extendModules {
              modules = [
                ({ ... }: {
                  users.users.root.openssh.authorizedKeys.keys = lib.mkForce [ ];
                })
              ];
            }).config.system.build.sdImage;
          };
          key = "github:thymis-io/thymis/image-formats.nix:sd-card-image";
        };
      nixos-vm = { config, inputs, pkgs, modulesPath, extendModules, ... }:
        let
          cfg = config.virtualisation;
          regInfo = pkgs: pkgs.closureInfo { rootPaths = config.virtualisation.additionalPaths; };
          rootFilesystemLabel = "nixos";
          selectPartitionTableLayout =
            { useEFIBoot, useDefaultFilesystems }:
            if useDefaultFilesystems then if useEFIBoot then "efi" else "legacy" else "none";
          systemImage = hostPkgs: import "${inputs.nixpkgs}/nixos/lib/make-disk-image.nix" {
            inherit pkgs config lib;
            additionalPaths = [ (regInfo hostPkgs) ];
            format = "qcow2";
            onlyNixStore = false;
            label = rootFilesystemLabel;
            partitionTableType = selectPartitionTableLayout { inherit (cfg) useDefaultFilesystems useEFIBoot; };
            installBootLoader = cfg.installBootLoader;
            touchEFIVars = cfg.useEFIBoot;
            diskSize = "auto";
            additionalSpace = "0M";
            copyChannel = false;
            OVMF = cfg.efi.OVMF;
          };
        in
        {
          imports = [
            "${modulesPath}/virtualisation/qemu-vm.nix"
          ];
          # system.build.thymis-image = config.system.build.vm;
          virtualisation.useBootLoader = true;
          virtualisation.useEFIBoot = true;
          boot.growPartition = true;
          boot.loader.systemd-boot.enable = true;
          # Mount the EFI System Partition at /boot so switch-to-configuration-ng
          # can update boot entries.  qemu-vm.nix with useBootLoader=true sets
          # useDefaultFilesystems=false, which means no /boot fstab entry is
          # generated automatically.  Without this mount the systemd-boot builder's
          # check-mountpoints script exits 1, causing switch-to-configuration switch
          # to fail in NixOS 25.11 (where the exit-status bug was fixed by nixpkgs
          # PR #369867).  The ESP label "ESP" is hard-coded by make-disk-image.nix.
          fileSystems."/boot" = lib.mkDefault {
            device = "/dev/disk/by-label/ESP";
            fsType = "vfat";
            options = [ "umask=0077" ];
          };
          system.build.thymis-image-with-secrets-builder-aarch64 =
            let
              hostPkgs = inputs.nixpkgs.legacyPackages.aarch64-linux;
              variant = extendModules {
                modules = [{ virtualisation.host.pkgs = hostPkgs; }];
              };
            in
            image-with-secrets-builder {
              pkgs = hostPkgs;
              image-path = systemImage hostPkgs;
              start-vm = "${variant.config.system.build.vm}/bin/run-${config.system.name}-vm";
            };
          system.build.thymis-image-with-secrets-builder-x86_64 =
            let
              hostPkgs = inputs.nixpkgs.legacyPackages.x86_64-linux;
              variant = extendModules {
                modules = [{ virtualisation.host.pkgs = hostPkgs; }];
              };
            in
            image-with-secrets-builder {
              pkgs = hostPkgs;
              image-path = systemImage hostPkgs;
              start-vm = "${variant.config.system.build.vm}/bin/run-${config.system.name}-vm";
            };
          key = "github:thymis-io/thymis/image-formats.nix:nixos-vm";
        };
      usb-stick-installer = { config, inputs, pkgs, extendModules, modulesPath, ... }:
        let
          variant = extendModules {
            modules = [
              {
                boot.kernelParams = [ "systemd.unit=getty.target" ];
                console = {
                  earlySetup = true;
                  font = "ter-v16n";
                  packages = [ pkgs.terminus_font ];
                };
                isoImage.isoName = "${variant.config.isoImage.isoBaseName}-${config.system.nixos.label}-${pkgs.stdenv.hostPlatform.system}.iso";
                isoImage.makeEfiBootable = true;
                isoImage.makeUsbBootable = true;
                isoImage.squashfsCompression = "zstd -Xcompression-level 15"; # xz takes forever

                isoImage.forceTextMode = true;
                boot.loader.timeout = lib.mkForce 1;

                systemd.services."getty@tty1" = {
                  overrideStrategy = "asDropin";
                  serviceConfig = {
                    ExecStart = [ "" installerFailsafe ];
                    Restart = "no";
                    StandardInput = "null";
                  };
                };
                disko.devices = lib.mkForce { };
                boot.loader.systemd-boot.enable = lib.mkForce false;
              }
              (modulesPath + "/installer/cd-dvd/iso-image.nix")
              (modulesPath + "/profiles/all-hardware.nix")
            ];
          };
          installer = pkgs.writeShellApplication {
            name = "installer";
            runtimeInputs = with pkgs; [
              dosfstools
              e2fsprogs
              gawk
              nixos-install-tools
              util-linux
              config.nix.package
            ];
            text = ''
              set -euo pipefail

              echo "Setting up disks..."
              for i in $(lsblk -pln -o NAME,TYPE | grep disk | awk '{ print $1 }'); do
                if [[ "$i" == "/dev/fd0" ]]; then
                  echo "$i is a floppy, skipping..."
                  continue
                fi
                if grep -ql "^$i" <(mount); then
                  echo "$i is in use, skipping..."
                else
                  DEVICE_MAIN="$i"
                  break
                fi
              done
              if [[ -z "$DEVICE_MAIN" ]]; then
                echo "ERROR: No usable disk found on this machine!"
                exit 1
              else
                echo "Found $DEVICE_MAIN, erasing..."
              fi

              DISKO_DEVICE_MAIN=''${DEVICE_MAIN#"/dev/"} ${config.system.build.diskoScript} 2> /dev/null

              echo "Installing the system..."
              nixos-install --no-channel-copy --no-root-password --option substituters "" --system ${config.system.build.toplevel}

              # copy thymis- prefixed files from /boot, /efi, /boot/efi to the new /mnt/boot
              mkdir -p /mnt/boot
              cp -r /iso/thymis-* /mnt/boot


              echo "Done! Rebooting..."
              sleep 3
              reboot
            '';
          };
          installerFailsafe = pkgs.writeShellScript "failsafe" ''
            ${lib.getExe installer} || echo "ERROR: Installation failure!"
            sleep 3600
          '';

        in
        {
          imports = [
            inputs.thymis.inputs.disko.nixosModules.disko
          ];
          disko.devices = {
            disk = {
              main = {
                device = "/dev/$DISKO_DEVICE_MAIN";
                type = "disk";
                content = {
                  type = "gpt";
                  partitions = {
                    ESP = {
                      type = "EF00";
                      size = "1G";
                      content = {
                        type = "filesystem";
                        format = "vfat";
                        mountpoint = "/boot";
                        mountOptions = [ "fmask=0022" "dmask=0022" ];
                      };
                    };
                    root = {
                      size = "100%";
                      content = {
                        type = "filesystem";
                        format = "ext4";
                        mountpoint = "/";
                        mountOptions = [ "noatime" ];
                      };
                    };
                  };
                };
              };
            };
          };
          boot.loader.systemd-boot.enable = true;
          boot.loader.efi.canTouchEfiVariables = true;

          system.build.thymis-image-with-secrets-builder-aarch64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.aarch64-linux;
            image-path = variant.config.system.build.isoImage;
          };
          system.build.thymis-image-with-secrets-builder-x86_64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.x86_64-linux;
            image-path = variant.config.system.build.isoImage;
          };
          key = "github:thymis-io/thymis/image-formats.nix:usb-stick-installer";
        };
    };
in
imageFormats
