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

      cp --no-preserve=mode,ownership "$IMAGE" "$FINAL_IMAGE_DESTINATION"

      echo "Final image: $FINAL_IMAGE_DESTINATION"
      PARTED_OUTPUT=$(${pkgs.parted}/bin/parted --json -s "$FINAL_IMAGE_DESTINATION" print)
      echo "Parted output: $PARTED_OUTPUT"
      FIRST_FAT_PARTITION_IDX=$(echo "$PARTED_OUTPUT" | ${pkgs.jq}/bin/jq -r '.disk.partitions[] | select(.filesystem == "fat16") | .number' | head -n 1)
      echo "First FAT partition index: $FIRST_FAT_PARTITION_IDX"
      eval "$(${pkgs.util-linux}/bin/partx "$FINAL_IMAGE_DESTINATION" -o START,SECTORS --nr "$FIRST_FAT_PARTITION_IDX" --pairs)"
      echo "First FAT partition starts at $START and has $SECTORS sectors"
      FIRST_FAT_PARTITION_START=$START
      FIRST_FAT_PARTITION_SECTORS=$SECTORS


      echo "Extracting first FAT partition to $TMPDIR/image_first_fat_partition"

      # dd if="$1" of="$2" conv=notrunc skip="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS"
      dd if="$FINAL_IMAGE_DESTINATION" of="$TMPDIR/image_first_fat_partition" conv=notrunc skip="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS"

      echo "Extracted first FAT partition to $TMPDIR/image_first_fat_partition"

      secrets_dir_abs=$(realpath "$secret_dir")

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

      echo "Final image: $FINAL_IMAGE_DESTINATION"

      if [ -n "$start_vm" ]; then
        START_VM_SCRIPT="$TMPDIR/start-vm"

        # insert "-b $FINAL_IMAGE_DESTINATION" to replace previous "-b whatever/nixos.qcow2"
        sed -e "s@-b .*nixos.qcow2@-b \"$FINAL_IMAGE_DESTINATION\"@" "$start_vm" > "$START_VM_SCRIPT"

        cp "$START_VM_SCRIPT" "$final_image_destination_base.start-vm"

        chmod +x "$final_image_destination_base.start-vm"
        echo "Start VM script: $final_image_destination_base.start-vm"
      fi

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
      sd-card-image = { config, pkgs, modulesPath, extendModules, ... }:
        let
          rootfsImage = hostPkgs: hostPkgs.callPackage "${modulesPath}/../lib/make-ext4-fs.nix" ({
            inherit (config.sdImage) storePaths;
            compressImage = false;
            populateImageCommands = config.sdImage.populateRootCommands;
            volumeLabel = "NIXOS_SD";
          } // lib.optionalAttrs (config.sdImage.rootPartitionUUID != null) {
            uuid = config.sdImage.rootPartitionUUID;
          });
          sdImage = config: hostPkgs: hostPkgs.callPackage
            ({ stdenv, dosfstools, e2fsprogs, mtools, libfaketime, util-linux, zstd }:
              stdenv.mkDerivation {
                name = config.sdImage.imageName;

                nativeBuildInputs =
                  [ dosfstools e2fsprogs mtools libfaketime util-linux zstd ];

                inherit (config.sdImage) compressImage;

                buildCommand = ''
                  mkdir -p $out/nix-support $out/sd-image
                  export img=$out/sd-image/${config.sdImage.imageName}

                  echo "${pkgs.stdenv.buildPlatform.system}" > $out/nix-support/system
                  if test -n "$compressImage"; then
                    echo "file sd-image $img.zst" >> $out/nix-support/hydra-build-products
                  else
                    echo "file sd-image $img" >> $out/nix-support/hydra-build-products
                  fi

                  # echo "Decompressing rootfs image"
                  # zstd -d --no-progress "${rootfsImage hostPkgs}" -o ./root-fs.img
                  cp "${rootfsImage hostPkgs}" ./root-fs.img

                  # Gap in front of the first partition, in MiB
                  gap=${toString config.sdImage.firmwarePartitionOffset}

                  # Create the image file sized to fit /boot/firmware and /, plus slack for the gap.
                  rootSizeBlocks=$(du -B 512 --apparent-size ./root-fs.img | awk '{ print $1 }')
                  firmwareSizeBlocks=$((${
                    toString config.sdImage.firmwareSize
                  } * 1024 * 1024 / 512))
                  imageSize=$((rootSizeBlocks * 512 + firmwareSizeBlocks * 512 + gap * 1024 * 1024))
                  truncate -s $imageSize $img

                  # type=b is 'W95 FAT32', type=83 is 'Linux'.
                  # The "bootable" partition is where u-boot will look file for the bootloader
                  # information (dtbs, extlinux.conf file).
                  sfdisk $img <<EOF
                      label: dos
                      label-id: ${config.sdImage.firmwarePartitionID}

                      start=''${gap}M, size=$firmwareSizeBlocks, type=b
                      start=$((gap + ${
                        toString config.sdImage.firmwareSize
                      }))M, type=83, bootable
                  EOF

                  # Copy the rootfs into the SD image
                  eval $(partx $img -o START,SECTORS --nr 2 --pairs)
                  dd conv=notrunc if=./root-fs.img of=$img seek=$START count=$SECTORS

                  # Create a FAT32 /boot/firmware partition of suitable size into firmware_part.img
                  eval $(partx $img -o START,SECTORS --nr 1 --pairs)
                  truncate -s $((SECTORS * 512)) firmware_part.img
                  faketime "1970-01-01 00:00:00" mkfs.vfat -i ${config.sdImage.firmwarePartitionID} -n ${config.raspberry-pi-nix.firmware-partition-label} firmware_part.img

                  # Populate the files intended for /boot/firmware
                  mkdir firmware
                  ${config.sdImage.populateFirmwareCommands}

                  # Copy the populated /boot/firmware into the SD image
                  (cd firmware; mcopy -psvm -i ../firmware_part.img ./* ::)
                  # Verify the FAT partition before copying it.
                  fsck.vfat -vn firmware_part.img
                  dd conv=notrunc if=firmware_part.img of=$img seek=$START count=$SECTORS

                  ${config.sdImage.postBuildCommands}

                  if test -n "$compressImage"; then
                      zstd -T$NIX_BUILD_CORES --rm $img
                  fi
                '';
              })
            { };

        in
        {
          imports = [
            inputs.nixos-generators.nixosModules.sd-aarch64
            "${inputs.raspberry-pi-nix}/sd-image/default.nix"
          ];
          sdImage.compressImage = false;
          system.build.thymis-image-with-secrets-builder-aarch64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.aarch64-linux;
            image-path = (extendModules {
              modules = [
                ({ config, ... }: {
                  users.users.root.openssh.authorizedKeys.keys = lib.mkForce [ ];
                  system.build.sdImage = lib.mkForce (sdImage config inputs.nixpkgs.legacyPackages.aarch64-linux);
                })
              ];
            }).config.system.build.sdImage;
          };
          system.build.thymis-image-with-secrets-builder-x86_64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.x86_64-linux;
            image-path = (extendModules {
              modules = [
                ({ config, ... }: {
                  users.users.root.openssh.authorizedKeys.keys = lib.mkForce [ ];
                  system.build.sdImage = lib.mkForce (sdImage config inputs.nixpkgs.legacyPackages.x86_64-linux);
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

                systemd.services."getty@tty1" = {
                  overrideStrategy = "asDropin";
                  serviceConfig = {
                    ExecStart = [ "" installerFailsafe ];
                    Restart = "no";
                    StandardInput = "null";
                  };
                };
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
              cp -r /boot/thymis-* /mnt/boot
              cp -r /efi/thymis-* /mnt/boot
              cp -r /boot/efi/thymis-* /mnt/boot

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
