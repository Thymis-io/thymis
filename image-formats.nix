args@{ ... }:
let
  inherit (args) inputs lib;
  image-with-secrets-builder = { pkgs, image-path }: pkgs.callPackage
    ({}: pkgs.writeShellScript "fill-image-with-secrets" ''
      #! ${pkgs.runtimeShell}
      set -euo pipefail
      set -x

      if [ -z "''${2:-}" ]; then
        echo "Usage: $0 <secret_dir> <final_image_destination>"
        exit 1
      fi

      image_dir=${image-path}
      secret_dir="$1"
      final_image_destination="$2"

      if [ ! -d "$secret_dir" ]; then
        echo "Secret directory does not exist: $secret_dir"
        exit 1
      fi

      if [ ! -d "$image_dir" ]; then
        echo "Image directory does not exist: $image_dir"
        exit 1
      fi

      IMAGE_ENDINGS="qcow2 img"
      for ENDING in $IMAGE_ENDINGS; do
        IMAGE_WITH_ENDING=$(find "$image_dir" -name "*.$ENDING" -type f | head -n 1)
        if ! [ -z "$IMAGE_WITH_ENDING" ]; then
          IMAGE="$IMAGE_WITH_ENDING"
        fi
      done

      if [ -z "''${IMAGE:-}" ]; then
        echo "No image found in $image_dir"
        exit 1
      fi

      if ! file "$IMAGE" | grep -q -e "DOS/MBR boot sector"; then
        file "$IMAGE"
        echo "Image is not a bootable image"
        exit 1
      fi

      echo "Image: $IMAGE"

      cp $IMAGE $final_image_destination --no-preserve=mode,ownership

      echo "Final image: $final_image_destination"
      PARTED_OUTPUT=$(${pkgs.parted}/bin/parted --json -s "$final_image_destination" "print")
      echo "Parted output: $PARTED_OUTPUT"
      FIRST_FAT_PARTITION_IDX=$(echo "$PARTED_OUTPUT" | ${pkgs.jq}/bin/jq -r '.disk.partitions[] | select(.filesystem == "fat16") | .number' | head -n 1)
      echo "First FAT partition index: $FIRST_FAT_PARTITION_IDX"
      eval "$(${pkgs.util-linux}/bin/partx "$final_image_destination" -o START,SECTORS --nr "$FIRST_FAT_PARTITION_IDX" --pairs)"
      echo "First FAT partition starts at $START and has $SECTORS sectors"
      FIRST_FAT_PARTITION_START=$START
      FIRST_FAT_PARTITION_SECTORS=$SECTORS

      TMPDIR=$(mktemp -d)
      trap 'rm -rf "$TMPDIR"' EXIT

      echo "Extracting first FAT partition to $TMPDIR/image_first_fat_partition"

      # dd if="$1" of="$2" conv=notrunc skip="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS"
      dd if="$final_image_destination" of="$TMPDIR/image_first_fat_partition" conv=notrunc skip="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS"

      echo "Extracted first FAT partition to $TMPDIR/image_first_fat_partition"

      secrets_dir_abs=$(realpath "$secret_dir")

      echo "Checking FAT partition"

      setsid ${pkgs.dosfstools}/bin/fsck.vfat -vn "$TMPDIR/image_first_fat_partition"

      echo "Copying secrets to FAT partition"

      (cd "$secrets_dir_abs" && (setsid ${pkgs.mtools}/bin/mcopy -psvm -i "$TMPDIR/image_first_fat_partition" ./* ::) </dev/null) || (echo "mcopy failed, most probably due to file name conflicts"; exit 1)

      echo "Copying secrets to FAT partition done"

      dd if="$TMPDIR/image_first_fat_partition" of="$final_image_destination" conv=notrunc seek="$FIRST_FAT_PARTITION_START" count="$FIRST_FAT_PARTITION_SECTORS" status=progress


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
      sd-card-image = { config, pkgs, modulesPath, ... }:
        let
          rootfsImage = hostPkgs: hostPkgs.callPackage "${modulesPath}/../lib/make-ext4-fs.nix" ({
            inherit (config.sdImage) storePaths;
            compressImage = false;
            populateImageCommands = config.sdImage.populateRootCommands;
            volumeLabel = "NIXOS_SD";
          } // lib.optionalAttrs (config.sdImage.rootPartitionUUID != null) {
            uuid = config.sdImage.rootPartitionUUID;
          });
          sdImage = hostPkgs: hostPkgs.callPackage
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
          # system.build.thymis-image = config.system.build.sdImage;
          system.build.thymis-image-with-secrets-builder-aarch64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.aarch64-linux;
            image-path = sdImage inputs.nixpkgs.legacyPackages.aarch64-linux;
          };
          system.build.thymis-image-with-secrets-builder-x86_64 = image-with-secrets-builder {
            pkgs = inputs.nixpkgs.legacyPackages.x86_64-linux;
            image-path = sdImage inputs.nixpkgs.legacyPackages.x86_64-linux;
          };
          key = "github:thymis-io/thymis/image-formats.nix:sd-card-image";
        };
      # nixos-vm = { config, modulesPath, ... }: {
      #   imports = [
      #     "${modulesPath}/virtualisation/qemu-vm.nix"
      #   ];
      #   # system.build.thymis-image = config.system.build.vm;
      #   key = "github:thymis-io/thymis/image-formats.nix:nixos-vm";
      # };
    };
in
imageFormats
