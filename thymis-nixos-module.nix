{ config, lib, pkgs, inputs, modulesPath, ... }:
let
  cfg = config.thymis.config;
  controllerCfg = config.thymis.controller;
  use-wifi = cfg.wifi-ssid != "" && cfg.wifi-password != "";
  # Define the settings format used for this program
  settingsFormat = pkgs.formats.json { };
in

{
  imports = [
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
          device-name = lib.mkOption {
            type = lib.types.str;
            default = "thymis";
            description = "Name of the device";
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
    thymis.controller = {
      enable = lib.mkEnableOption "the Thymis controller";
      repo-dir = lib.mkOption {
        type = lib.types.str;
        default = "/var/lib/thymis";
        description = "Directory where the controller will store its state";
      };
    };
  };
  config = lib.mkMerge [
    {
      nix.settings.experimental-features = [ "nix-command" "flakes" ];
      users.users.root.password = cfg.password;
      services.openssh = {
        enable = true;
        settings.PermitRootLogin = "yes";
      };
      networking.hostName = cfg.device-name;
      networking.wireless = lib.mkIf use-wifi {
        enable = true;
        networks = {
          "${cfg.wifi-ssid}" = {
            psk = "${cfg.wifi-password}";
          };
        };
      };
      boot.supportedFilesystems = lib.mkForce [ "btrfs" "cifs" "f2fs" "jfs" "ntfs" "reiserfs" "vfat" "xfs" "ext4" ];
      services.getty.greetingLine = ''<<< Welcome to Thymis - NixOS ${config.system.nixos.label} (\m) - \l >>>'';
      services.getty.helpLine = lib.mkForce ''
        This is a Thymis device. You can login as root with the password you set during installation.
      '';
      system.nixos.distroName = "Thymis - NixOS";
      services.getty.autologinUser = lib.mkForce null;
      services.xserver.enable = true;
      systemd.services.display-manager.restartIfChanged = lib.mkForce true;
      users.users.nixos = {
        isNormalUser = true;
        createHome = true;
        password = cfg.password;
      };
      networking.firewall = {
        allowedTCPPorts = [ 22 3000 ];
      };
    }
    (lib.mkIf controllerCfg.enable {
      environment.systemPackages = [
        pkgs.git
      ];
      systemd.services.thymis-controller = {
        description = "Thymis controller";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-controller}/bin/thymis-controller";
        path = [
          "/run/current-system/sw"
          pkgs.git
        ];
        environment = {
          REPO_PATH = controllerCfg.repo-dir;
        };
      };
      systemd.services.thymis-frontend = {
        description = "Thymis frontend";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-frontend}/bin/thymis-frontend";
        environment = {
          HOST = "127.0.0.1";
          PORT = "3000";
          PUBLIC_CONTROLLER_HOST = "127.0.0.1:8000";
        };
        path = [
          "/run/current-system/sw"
        ];
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
      services.xserver.displayManager.sddm.enable = true;
      services.xserver.displayManager.autoLogin.enable = true;
      services.xserver.displayManager.autoLogin.user = "nixos";
      services.xserver.windowManager.i3.enable = true;
      services.xserver.windowManager.i3.configFile = pkgs.writeText "i3-config" ''
        # i3 config file (v4)
        bar mode invisible;
        exec ${pkgs.firefox}/bin/firefox --kiosk http://localhost:3000/kiosk
      '';
      networking.firewall.allowedTCPPorts = [ 80 443 8000 ];
    })
  ];
}
