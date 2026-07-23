{ lib, image-with-secrets-builder }:
{ config, pkgs, modulesPath, ... }:
let
  cfg = config.thymis.imageBasedUpdates;
  inherit (pkgs.stdenv.hostPlatform) efiArch;
  imageBaseName = "${cfg.imageId}_${cfg.version}";
  splitStoreImage = "${config.system.build.image}/${imageBaseName}.nix-store.raw";
  ukiFile = config.system.boot.loader.ukiFile;
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
      description = "Monotonically increasing systemd-compatible image version.";
    };

    storeSize = lib.mkOption {
      type = lib.types.str;
      default = "4G";
      description = "Fixed size of each immutable Nix store slot.";
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

  config = {
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
        assertion = cfg.updateUrl == null || cfg.allowInsecureUpdates || lib.hasPrefix "https://" cfg.updateUrl;
        message = "A/B update URLs must use HTTPS unless allowInsecureUpdates is enabled";
      }
      {
        assertion = cfg.updateUrl == null || cfg.allowInsecureUpdates || cfg.verifyUpdates;
        message = "A/B update signature verification may only be disabled when allowInsecureUpdates is enabled";
      }
      {
        assertion = cfg.updateUrl == null || !cfg.verifyUpdates || cfg.updatePublicKey != null;
        message = "A/B updates with signature verification require updatePublicKey";
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
      "/boot" = {
        device = "/dev/disk/by-partlabel/${cfg.imageId}-boot";
        fsType = "vfat";
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
      partitions = {
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

        "20-nix-store" = {
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

        "30-empty-store".repartConfig = {
          Type = "linux-generic";
          Label = "_empty";
          Minimize = "off";
          SizeMinBytes = cfg.storeSize;
          SizeMaxBytes = cfg.storeSize;
          SplitName = "-";
        };

        "40-data".repartConfig = {
          Type = "root";
          Label = "${cfg.imageId}-data";
          Format = "ext4";
          Minimize = "off";
          SizeMinBytes = cfg.dataSize;
          GrowFileSystem = "yes";
          SplitName = "-";
        };
      };
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
      transfers = {
        "10-nix-store" = {
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

        "20-boot-image" = {
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
      };
    };

    systemd.timers.systemd-sysupdate.wantedBy = lib.mkIf
      (cfg.updateUrl != null && !cfg.automaticUpdates)
      (lib.mkForce [ ]);

    environment.etc = lib.mkIf (cfg.updatePublicKey != null) {
      "systemd/import-pubring.pgp".source = cfg.updatePublicKey;
    };

    system.build.thymis-sysupdate-package = pkgs.runCommand
      "thymis-sysupdate-package-${cfg.version}"
      { nativeBuildInputs = [ pkgs.coreutils pkgs.zstd ]; }
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

    system.build.thymis-image-with-secrets-builder = image-with-secrets-builder {
      inherit pkgs;
      image-path = config.system.build.image;
    };
    system.build.thymis-image-with-secrets-builder-aarch64 =
      config.system.build.thymis-image-with-secrets-builder;
    system.build.thymis-image-with-secrets-builder-x86_64 =
      config.system.build.thymis-image-with-secrets-builder;
  };
}
