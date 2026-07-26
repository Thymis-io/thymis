{ lib, image-with-secrets-builder }:
args@{ config, pkgs, modulesPath, options, ... }:
let
  inputs = args.inputs or { };
  cfg = config.thymis.imageBasedUpdates;
  packageSetFor =
    system: lib.attrByPath [ "nixpkgs" "legacyPackages" system ] pkgs inputs;
  imageBaseName = "${cfg.imageId}_${cfg.version}";
  splitStoreImage = "${config.system.build.image}/${imageBaseName}.nix-store.raw";
  hasRaspberryPiBootloaderOption =
    lib.hasAttrByPath [ "boot" "loader" "raspberry-pi" "bootloader" ] options;
  isRaspberryPi = lib.attrByPath [ "boot" "loader" "raspberry-pi" "enable" ] false config;
  efiArch = pkgs.stdenv.hostPlatform.efiArch;
  ukiFile = config.system.boot.loader.ukiFile;
  splitBootImage = "${config.system.build.image}/${imageBaseName}.boot.raw";
  embeddedUpdatePublicKey = pkgs.runCommand "thymis-image-update-key.pgp"
    { nativeBuildInputs = [ pkgs.buildPackages.coreutils ]; }
    ''
      base64 --decode ${pkgs.writeText "thymis-image-update-key.base64" cfg.updatePublicKeyBase64} > "$out"
    '';

  raspberryPiBootTree = pkgs.runCommand "${imageBaseName}-raspberry-pi-boot" { } ''
    mkdir -p "$out"
    ${config.boot.loader.raspberry-pi.firmwarePopulateCmd} \
      -c ${config.system.build.toplevel} \
      -f "$out"
  '';

  raspberryPiAutoboot = pkgs.writeText "autoboot.txt" ''
    [all]
    tryboot_a_b=1
    boot_partition=2

    [tryboot]
    boot_partition=3
  '';

  raspberryPiAbTool = pkgs.writeShellApplication {
    name = "thymis-ab";
    runtimeInputs = [ pkgs.coreutils pkgs.jq pkgs.systemd ];
    text = ''
            set -euo pipefail

            read_dt_integer() {
              local path="$1"
              local hex
              if [[ ! -r "$path" ]]; then
                return
              fi
              hex="$(od -An -N4 -tx1 "$path" | tr -d ' \n')"
              if [[ "''${#hex}" == 8 ]]; then
                printf '%d' "$((16#$hex))"
              fi
            }

            current_partition() {
              read_dt_integer /proc/device-tree/chosen/bootloader/partition
            }

            tryboot_active() {
              [[ "$(read_dt_integer /proc/device-tree/chosen/bootloader/tryboot)" == "1" ]]
            }

            status() {
              local partition tryboot version
              partition="$(current_partition)"
              tryboot=false
              if tryboot_active; then
                tryboot=true
              fi
              # shellcheck disable=SC1091
              version="$(. /etc/os-release; printf '%s' "''${IMAGE_VERSION:-unknown}")"
              jq -n \
                --arg strategy raspberry-pi-tryboot \
                --arg image_id ${lib.escapeShellArg cfg.imageId} \
                --arg version "$version" \
                --arg partition "$partition" \
                --argjson trial "$tryboot" \
                '{strategy: $strategy, image_id: $image_id, version: $version, boot_partition: $partition, trial: $trial}'
            }

            commit() {
              local partition other tmp normal section line
              partition="$(current_partition)"
              case "$partition" in
                2) other=3 ;;
                3) other=2 ;;
                *)
                  echo "Refusing to commit unexpected boot partition: $partition" >&2
                  exit 1
                  ;;
              esac
              if ! tryboot_active; then
                normal=
                section=
                while IFS= read -r line; do
                  case "$line" in
                    "[all]") section=all ;;
                    "["*"]") section= ;;
                    boot_partition=*)
                      if [[ "$section" == all ]]; then
                        normal="''${line#boot_partition=}"
                        break
                      fi
                      ;;
                  esac
                done < /boot/firmware/autoboot.txt
                if [[ "$normal" == "$partition" ]]; then
                  return
                fi
                echo "Refusing to commit: the current boot is not a tryboot" >&2
                exit 1
              fi
              tmp=/boot/firmware/autoboot.txt.new
              cat > "$tmp" <<EOF
      [all]
      tryboot_a_b=1
      boot_partition=$partition

      [tryboot]
      boot_partition=$other
      EOF
              mv "$tmp" /boot/firmware/autoboot.txt
              sync /boot/firmware
            }

            stage() {
              updatectl update
              sync
              reboot "0 tryboot"
            }

            case "''${1:-status}" in
              status) status ;;
              stage) stage ;;
              commit) commit ;;
              *)
                echo "Usage: thymis-ab {status|stage|commit}" >&2
                exit 2
                ;;
            esac
    '';
  };
  systemdBootCommit = pkgs.writeShellScriptBin "thymis-ab-commit" ''
    exec ${pkgs.systemd}/lib/systemd/systemd-bless-boot good
  '';


  storePartition = {
    storePaths = [ config.system.build.toplevel ];
    nixStorePrefix = "/";
    repartConfig = {
      Type = "linux-generic";
      Label = imageBaseName;
      Format = "squashfs";
      Compression = "zstd";
      Minimize = "off";
      SizeMinBytes = cfg.storeSize;
      SizeMaxBytes = cfg.storeSize;
      ReadOnly = "yes";
      SplitName = "nix-store";
    };
  };

  emptyStorePartition.repartConfig = {
    Type = "linux-generic";
    Label = "_empty";
    Minimize = "off";
    SizeMinBytes = cfg.storeSize;
    SizeMaxBytes = cfg.storeSize;
    SplitName = "-";
  };

  dataPartition.repartConfig = {
    Type = "root";
    Label = "${cfg.imageId}-data";
    Format = "ext4";
    Minimize = "off";
    SizeMinBytes = cfg.dataSize;
    GrowFileSystem = "yes";
    SplitName = "-";
  };

  storeTransfer = {
    Transfer = {
      ProtectVersion = "%A";
      Verify = cfg.verifyUpdates;
    };
    Source = {
      Type = "url-file";
      Path = cfg.updateUrl;
      MatchPattern = [ "${cfg.imageId}_@v.nix-store.raw.zst" ];
    };
    Target = {
      Type = "partition";
      Path = "auto";
      MatchPattern = "${cfg.imageId}_@v";
      MatchPartitionType = "linux-generic";
      ReadOnly = true;
      InstancesMax = 2;
    };
  };
in
{
  imports = [
    (modulesPath + "/image/repart.nix")
    (modulesPath + "/profiles/image-based-appliance.nix")
  ];

  options.thymis.imageBasedUpdates = {
    imageId = lib.mkOption {
      type = lib.types.str;
      default = "thymis";
      description = "Stable image identifier used in update artifact names and partition labels.";
    };

    version = lib.mkOption {
      type = lib.types.str;
      default = "${toString (lib.attrByPath [ "self" "lastModified" ] 1 inputs)}.${toString (lib.attrByPath [ "self" "revCount" ] 0 inputs)}";
      description = "Monotonically increasing systemd-compatible image version.";
    };

    storeSize = lib.mkOption {
      type = lib.types.str;
      default = "4G";
      description = "Fixed size of each immutable Nix store slot.";
    };

    bootSize = lib.mkOption {
      type = lib.types.str;
      default = "1G";
      description = "Fixed size of each Raspberry Pi firmware and kernel slot.";
    };

    dataSize = lib.mkOption {
      type = lib.types.str;
      default = "4G";
      description = "Minimum size of the persistent writable root partition.";
    };

    updateUrl = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Base HTTPS URL containing systemd-sysupdate artifacts and manifests.";
    };

    updatePublicKey = lib.mkOption {
      type = lib.types.nullOr lib.types.path;
      default = null;
      description = "OpenPGP public key used to verify the signed SHA256SUMS manifest.";
    };

    updatePublicKeyBase64 = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Base64-encoded binary OpenPGP public key used to verify the signed SHA256SUMS manifest.";
    };

    verifyUpdates = lib.mkOption {
      type = lib.types.bool;
      default = true;
      description = "Require systemd-sysupdate to verify update manifest signatures.";
    };

    allowInsecureUpdates = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Allow HTTP update URLs or disabled signature verification for local testing.";
    };

    automaticUpdates = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable the upstream systemd-sysupdate timer instead of controller-triggered updates.";
    };

    bootAttempts = lib.mkOption {
      type = lib.types.ints.positive;
      default = 3;
      description = "Boot attempts before systemd-boot falls back to the previous UKI.";
    };
  };

  config = lib.mkMerge [
    {
      assertions = [
        {
          assertion = builtins.match "[A-Za-z0-9][A-Za-z0-9-]*" cfg.imageId != null;
          message = "thymis.imageBasedUpdates.imageId may only contain ASCII letters, digits, and hyphens";
        }
        {
          assertion = builtins.match "[0-9][0-9A-Za-z.+~-]*" cfg.version != null;
          message = "thymis.imageBasedUpdates.version must start with a digit and be a systemd-compatible version";
        }
        {
          assertion = builtins.stringLength "${cfg.imageId}_${cfg.version}" <= 36;
          message = "the image ID and version must fit in a 36-character GPT partition label";
        }
        {
          assertion =
            !isRaspberryPi
            || builtins.stringLength "${cfg.imageId}-boot_${cfg.version}" <= 36;
          message = "the Raspberry Pi boot image ID and version must fit in a 36-character GPT partition label";
        }
        {
          assertion = cfg.updateUrl == null || cfg.allowInsecureUpdates || lib.hasPrefix "https://" cfg.updateUrl;
          message = "A/B update URLs must use HTTPS unless allowInsecureUpdates is enabled";
        }
        {
          assertion = cfg.updateUrl == null || cfg.allowInsecureUpdates || cfg.verifyUpdates;
          message = "A/B update signature verification may only be disabled when allowInsecureUpdates is enabled";
        }
        {
          assertion =
            cfg.updateUrl == null
            || !cfg.verifyUpdates
            || cfg.updatePublicKey != null
            || cfg.updatePublicKeyBase64 != null;
          message = "A/B updates with signature verification require updatePublicKey or updatePublicKeyBase64";
        }
      ];

      nix.gc.automatic = lib.mkForce false;

      system.image = {
        id = cfg.imageId;
        version = cfg.version;
      };

      boot.loader = {
        grub.enable = false;
        efi.canTouchEfiVariables = false;
      };

      fileSystems = {
        "/" = {
          device = "/dev/disk/by-partlabel/${cfg.imageId}-data";
          fsType = "ext4";
          options = [ "x-systemd.growfs" ];
        };
        "/nix/store" = {
          device = "/dev/disk/by-partlabel/${imageBaseName}";
          fsType = "squashfs";
          options = [ "ro" ];
        };
      };

      image.repart = {
        name = cfg.imageId;
        version = cfg.version;
        split = true;
      };

      boot.initrd.systemd.repart.enable = true;
      systemd.repart.partitions."40-data" = {
        Type = "root";
        Label = "${cfg.imageId}-data";
        Format = "ext4";
        SizeMinBytes = cfg.dataSize;
        GrowFileSystem = true;
      };

      systemd.sysupdate = lib.mkIf (cfg.updateUrl != null) {
        enable = true;
        reboot.enable = false;
        transfers."10-nix-store" = storeTransfer;
      };

      systemd.timers.systemd-sysupdate.wantedBy = lib.mkIf
        (cfg.updateUrl != null && !cfg.automaticUpdates)
        (lib.mkForce [ ]);

      environment.etc."systemd/import-pubring.pgp" = lib.mkIf
        (cfg.updatePublicKey != null || cfg.updatePublicKeyBase64 != null)
        {
          source =
            if cfg.updatePublicKey != null then
              cfg.updatePublicKey
            else
              embeddedUpdatePublicKey;
        };
      environment.etc."thymis/image-update-state".text = builtins.toJSON {
        strategy = if isRaspberryPi then "raspberry-pi-tryboot" else "systemd-boot";
        image_id = cfg.imageId;
        version = cfg.version;
      };

      system.build.thymis-image-with-secrets-builder = image-with-secrets-builder {
        inherit pkgs;
        image-path = config.system.build.image;
      };
      system.build.thymis-image-with-secrets-builder-aarch64 =
        image-with-secrets-builder {
          pkgs = packageSetFor "aarch64-linux";
          image-path = config.system.build.image;
        };
      system.build.thymis-image-with-secrets-builder-x86_64 =
        image-with-secrets-builder {
          pkgs = packageSetFor "x86_64-linux";
          image-path = config.system.build.image;
        };
    }

    (lib.mkIf isRaspberryPi {
      boot.loader = {
        systemd-boot.enable = false;
      } // lib.optionalAttrs hasRaspberryPiBootloaderOption {
        raspberry-pi.bootloader = lib.mkForce "kernel";
      };

      fileSystems."/boot/firmware" = {
        device = "/dev/disk/by-partlabel/${cfg.imageId}-control";
        fsType = "vfat";
        options = [ "noatime" ];
      };

      image.repart.partitions = {
        "05-control" = {
          contents."/autoboot.txt".source = raspberryPiAutoboot;
          repartConfig = {
            Type = "esp";
            Label = "${cfg.imageId}-control";
            Format = "vfat";
            Minimize = "off";
            SizeMinBytes = "64M";
            SizeMaxBytes = "64M";
            SplitName = "-";
          };
        };

        "10-boot-slot" = {
          contents."/".source = raspberryPiBootTree;
          repartConfig = {
            Type = "esp";
            Label = "${cfg.imageId}-boot_${cfg.version}";
            Format = "vfat";
            Minimize = "off";
            SizeMinBytes = cfg.bootSize;
            SizeMaxBytes = cfg.bootSize;
            SplitName = "boot";
          };
        };

        "15-empty-boot".repartConfig = {
          Type = "esp";
          Label = "_empty";
          Minimize = "off";
          SizeMinBytes = cfg.bootSize;
          SizeMaxBytes = cfg.bootSize;
          SplitName = "-";
        };

        "20-nix-store" = storePartition;
        "30-empty-store" = emptyStorePartition;
        "40-data" = dataPartition;
      };

      systemd.sysupdate.transfers."20-boot-partition" = lib.mkIf (cfg.updateUrl != null) {
        Transfer = {
          ProtectVersion = "%A";
          Verify = cfg.verifyUpdates;
        };
        Source = {
          Type = "url-file";
          Path = cfg.updateUrl;
          MatchPattern = [ "${cfg.imageId}_@v.boot.raw.zst" ];
        };
        Target = {
          Type = "partition";
          Path = "auto";
          MatchPattern = "${cfg.imageId}-boot_@v";
          MatchPartitionType = "esp";
          InstancesMax = 2;
        };
      };

      environment.systemPackages = [ raspberryPiAbTool ];

      system.build.thymis-sysupdate-package = pkgs.runCommand
        "thymis-sysupdate-package-${cfg.version}"
        { nativeBuildInputs = [ pkgs.buildPackages.coreutils pkgs.buildPackages.zstd ]; }
        ''
          mkdir -p "$out"
          zstd --no-progress --threads="$NIX_BUILD_CORES" -10 \
            "${splitStoreImage}" \
            -o "$out/${cfg.imageId}_${cfg.version}.nix-store.raw.zst"
          zstd --no-progress --threads="$NIX_BUILD_CORES" -10 \
            "${splitBootImage}" \
            -o "$out/${cfg.imageId}_${cfg.version}.boot.raw.zst"
          cd "$out"
          sha256sum --binary \
            "${cfg.imageId}_${cfg.version}.boot.raw.zst" \
            "${cfg.imageId}_${cfg.version}.nix-store.raw.zst" \
            > SHA256SUMS
        '';
    })

    (lib.mkIf (!isRaspberryPi) {
      # The controller blesses the trial after the agent reconnects.
      systemd.services.systemd-bless-boot.enable = false;
      environment.systemPackages = [ systemdBootCommit ];


      fileSystems."/boot" = {
        device = "/dev/disk/by-partlabel/${cfg.imageId}-boot";
        fsType = "vfat";
      };

      image.repart.partitions = {
        "10-esp" = {
          contents = {
            "/EFI/BOOT/BOOT${lib.toUpper efiArch}.EFI".source =
              "${pkgs.systemd}/lib/systemd/boot/efi/systemd-boot${efiArch}.efi";
            "/EFI/Linux/${ukiFile}".source = "${config.system.build.uki}/${ukiFile}";
            "/loader/loader.conf".source = builtins.toFile "loader.conf" ''
              timeout 3
            '';
          };
          repartConfig = {
            Type = "esp";
            Label = "${cfg.imageId}-boot";
            Format = "vfat";
            SizeMinBytes = "256M";
            SplitName = "-";
          };
        };

        "20-nix-store" = storePartition;
        "30-empty-store" = emptyStorePartition;
        "40-data" = dataPartition;
      };

      systemd.sysupdate.transfers."20-boot-image" = lib.mkIf (cfg.updateUrl != null) {
        Transfer = {
          ProtectVersion = "%A";
          Verify = cfg.verifyUpdates;
        };
        Source = {
          Type = "url-file";
          Path = cfg.updateUrl;
          MatchPattern = [ "${cfg.imageId}_@v.efi" ];
        };
        Target = {
          Type = "regular-file";
          Path = "/EFI/Linux";
          PathRelativeTo = "boot";
          MatchPattern = [
            "${cfg.imageId}_@v+@l-@d.efi"
            "${cfg.imageId}_@v+@l.efi"
            "${cfg.imageId}_@v.efi"
          ];
          Mode = "0444";
          TriesLeft = cfg.bootAttempts;
          TriesDone = 0;
          InstancesMax = 2;
        };
      };

      system.build.thymis-sysupdate-package = pkgs.runCommand
        "thymis-sysupdate-package-${cfg.version}"
        { nativeBuildInputs = [ pkgs.buildPackages.coreutils pkgs.buildPackages.zstd ]; }
        ''
          mkdir -p "$out"
          cp "${config.system.build.uki}/${ukiFile}" "$out/${cfg.imageId}_${cfg.version}.efi"
          zstd --no-progress --threads="$NIX_BUILD_CORES" -10 \
            "${splitStoreImage}" \
            -o "$out/${cfg.imageId}_${cfg.version}.nix-store.raw.zst"
          cd "$out"
          sha256sum --binary \
            "${cfg.imageId}_${cfg.version}.efi" \
            "${cfg.imageId}_${cfg.version}.nix-store.raw.zst" \
            > SHA256SUMS
        '';
    })
  ];
}
