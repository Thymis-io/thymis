{ config, lib, pkgs, inputs, modulesPath, ... }:
let
  cfg = config.thymis.config;
  use-wifi = cfg.wifi-ssid != "" && cfg.wifi-password != "";
  settingsFormat = pkgs.formats.json { };
in

{
  imports = [
    inputs.thymis.inputs.home-manager.nixosModules.default
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
          agent = lib.mkOption {
            type = lib.types.submodule {
              freeformType = settingsFormat.type;
              options = {
                enabled = lib.mkOption {
                  type = lib.types.bool;
                  default = false;
                  description = "Enable the agent";
                };
                controller-url = lib.mkOption {
                  type = lib.types.str;
                  default = "";
                  description = "URL of the Thymis Controller";
                };
              };
            };
          };
        };
      };
      default = { };
      description = "Thymis configuration";
    };
  };
  config = {
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
    systemd.services.display-manager.restartIfChanged = lib.mkForce true;
    users.users.thymis = {
      isNormalUser = true;
      createHome = true;
      password = cfg.password;
    };
    networking.firewall = {
      allowedTCPPorts = [ 22 ];
    };
    systemd.services.thymis-agent = lib.mkIf cfg.agent.enabled {
      description = "Thymis agent";
      after = [ "network.target" "sshd.service" ];
      wantedBy = [ "multi-user.target" ];
      script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-agent}/bin/thymis-agent";
      path = [
        "/run/current-system/sw"
      ];
      environment = {
        CONTROLLER_HOST = cfg.agent.controller-url;
      };
    };
  };
}
