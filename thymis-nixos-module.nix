{ config, lib, pkgs, inputs, modulesPath, thymis-config, ... }:
let
  cfg = config.thymis.config;
  use-wifi = cfg.wifi-ssid != "" && cfg.wifi-password != "";
  # Define the settings format used for this program
  settingsFormat = pkgs.formats.json { };
in
assert lib.assertMsg
  (builtins.elem thymis-config.device-type [ "generic-x86_64" "raspberry_pi_4b" ])
  "thymis-config.device-type must be one of [ \"generic-x86_64\" \"raspberry_pi_4b\" ]. Got ${thymis-config.device-type}";
{
  imports = (lib.optionals (thymis-config.device-type == "generic-x86_64") [
    "${modulesPath}/profiles/all-hardware.nix"
    # "${modulesPath}/installer/cd-dvd/iso-image.nix"
    "${modulesPath}/installer/cd-dvd/installation-cd-graphical-base.nix"
  ]) ++ (lib.optionals (thymis-config.device-type == "raspberry_pi_4b") [
    "${modulesPath}/installer/sd-card/sd-image-aarch64-installer.nix"
  ]) ++ [
    inputs.home-manager.nixosModules.default
    "${modulesPath}/profiles/base.nix"
  ];
  options = {
    thymis.config = lib.mkOption {
      type = lib.types.submodule {
        freeformType = settingsFormat.type;
        options = {
          device-type = lib.mkOption {
            type = lib.types.str;
            default = "generic-x86_64";
            description = "Type of the device";
          };
          hostname = lib.mkOption {
            type = lib.types.str;
            default = "thymis";
            description = "Hostname of the device";
          };
          password = lib.mkOption {
            type = lib.types.str;
            description = "Password for the root user";
          };
          wifi-ssid = lib.mkOption {
            type = lib.types.str;
            default = "";
            description = "SSID of the wifi network";
          };
          wifi-password = lib.mkOption {
            type = lib.types.str;
            default = "";
            description = "Password for the wifi network";
          };
        };
      };
      default = { };
      description = "Thymis configuration";
    };
  };
  config = lib.mkMerge [
    {
      thymis.config = thymis-config;
      system.build.download-path = lib.mkDefault (throw "thymis-config.system.build.download-path is not set");
      nix.settings.experimental-features = [ "nix-command" "flakes" ];
      users.users.root.password = cfg.password;
      services.openssh = {
        enable = true;
        settings.PermitRootLogin = "yes";
      };
      networking.hostName = cfg.hostname;
      networking.wireless = lib.mkIf use-wifi {
        enable = true;
        networks = {
          "${cfg.wifi-ssid}" = {
            psk = "${cfg.wifi-password}";
          };
        };
      };
      services.getty.greetingLine = ''<<< Welcome to Thymis - NixOS ${config.system.nixos.label} (\m) - \l >>>'';
      services.getty.helpLine = lib.mkForce ''
        This is a Thymis device. You can login as root with the password you set during installation.
      '';
      system.nixos.distroName = "Thymis - NixOS";
      services.getty.autologinUser = lib.mkForce null;
      services.xserver.displayManager = {
        gdm = {
          enable = true;
          autoSuspend = false;
        };
        autoLogin = {
          enable = true;
          user = "nixos";
        };
      };
      services.xserver.windowManager.i3.enable = true;
      services.xserver.windowManager.i3.configFile = pkgs.writeText "i3-config" ''
        bar mode invisible;
        exec ${pkgs.firefox}/bin/firefox --kiosk http://localhost:3000/kiosk
        '';
      systemd.services.thymis-frontend = {
        description = "Thymis frontend";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        script = "${inputs.self.packages.${config.nixpkgs.hostPlatform.system}.thymis-frontend}/bin/thymis-frontend";
        environment = {
          HOST = "127.0.0.1";
          PORT = "3000";
        };
      };
      systemd.services.thymis-controller = {
        description = "Thymis controller";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        script = "${inputs.self.packages.${config.nixpkgs.hostPlatform.system}.thymis-controller}/bin/thymis-controller";
      };
      services.nginx = {
        enable = true;
        virtualHosts.default = {
          default = true;
          locations."/" = {
            proxyPass = "http://localhost:3000";
            recommendedProxySettings = true;
          };
        };
      };
    }
    (lib.optionalAttrs (thymis-config.device-type == "generic-x86_64") {
      nixpkgs.hostPlatform = "x86_64-linux";
      isoImage.squashfsCompression = "lz4";
      isoImage.isoBaseName = "thymis-${cfg.hostname}";
      system.build.download-path = pkgs.writeText "download-path" (
        let
          drv = config.system.build.isoImage;
        in
        drv + "/iso/${drv.name}"
      );
    })
    (lib.optionalAttrs (thymis-config.device-type == "raspberry_pi_4b") {
      nixpkgs.hostPlatform = "aarch64-linux";
      sdImage.compressImage = false;
      sdImage.imageBaseName = "thymis-${cfg.hostname}";
      system.build.download-path = pkgs.writeText "download-path" (
        let
          drv = config.system.build.sdImage;
        in
        drv + "/sd-image/${drv.name}"
      );
    })
  ];

}
