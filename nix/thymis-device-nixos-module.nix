{ config, lib, pkgs, inputs, modulesPath, options, ... }:
let
  cfg = config.thymis.config;
  use-wifi = cfg.wifi-ssid != "" && (cfg.wifi-password != "" || cfg.wifi-auth != "");
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
            type = lib.types.nullOr lib.types.str;
            description = "Password for the root user";
            default = null;
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
          wifi-auth = lib.mkOption {
            type = lib.types.str;
            default = "";
            description = "Authentication method for the wifi network";
          };
          wifi-auth-protocols = lib.mkOption {
            type = lib.types.listOf (lib.types.submodule {
              options = {
                protocol = lib.mkOption {
                  type = lib.types.str;
                  default = "";
                  description = "Authentication protocol for the wifi network";
                };
              };
            });
            default = [ ];
            description = "Authentication protocols for the wifi network";
          };
          agent = lib.mkOption {
            type = lib.types.submodule {
              options = {
                enable = lib.mkOption {
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
    users.users.root.password = lib.mkIf (cfg.password != null) cfg.password;
    services.openssh = {
      enable = true;
      settings.PermitRootLogin = "yes";
    };
    networking.hostName = cfg.device-name;
    networking.wireless = lib.mkIf use-wifi {
      enable = true;
      networks = {
        "${cfg.wifi-ssid}" = {
          psk = lib.mkIf (cfg.wifi-password != "") cfg.wifi-password;
          auth = lib.mkIf (cfg.wifi-auth != "") cfg.wifi-auth;
          authProtocols = lib.mkIf (cfg.wifi-auth-protocols != [ ]) (map (x: x.protocol) cfg.wifi-auth-protocols);
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
      password = lib.mkIf (cfg.password != null) cfg.password;
    };
    networking.firewall = {
      allowedTCPPorts = [ 22 ];
    };
    networking.timeServers = options.networking.timeServers.default ++ [ "time.uni-paderborn.de" ];
    thymis.config.agent.enable = lib.mkDefault true;
    systemd.services.thymis-agent = lib.mkIf cfg.agent.enable {
      description = "Thymis agent";
      restartIfChanged = false;
      after = [ "network.target" "sshd.service" ];
      wantedBy = [ "multi-user.target" ];
      script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-agent}/bin/thymis-agent";
      path = [
        "/run/current-system/sw"
      ];
      environment = {
        CONTROLLER_HOST = cfg.agent.controller-url;
      };
      serviceConfig.Restart = "always";
      serviceConfig.Type = "notify";
    };
    system.activationScripts.thymis = lib.mkIf (cfg.agent.enable) {
      text = ''
        CONTROLLER_HOST=${cfg.agent.controller-url} ${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-agent}/bin/thymis-agent --just-place-secrets
      '';
    };
    system.activationScripts.users.deps = lib.mkIf (cfg.agent.enable) [ "thymis" ];

    documentation = {
      enable = lib.mkDefault false;
      doc.enable = lib.mkDefault false;
      info.enable = lib.mkDefault false;
      man.enable = lib.mkDefault false;
      nixos.enable = lib.mkDefault false;
    };
    environment = {
      # Perl is a default package.
      defaultPackages = lib.mkForce [ ];
      stub-ld.enable = lib.mkDefault false;
    };
    programs = {
      # The lessopen package pulls in Perl.
      less.lessopen = lib.mkDefault null;
      command-not-found.enable = lib.mkDefault false;
    };
    xdg.autostart.enable = lib.mkDefault false;
    xdg.icons.enable = lib.mkDefault false;
    xdg.mime.enable = lib.mkDefault false;
    xdg.sounds.enable = lib.mkDefault false;
    boot.enableContainers = lib.mkDefault false;
    services.udisks2.enable = lib.mkDefault false;
    services.speechd.enable = lib.mkForce false;
    nixpkgs.overlays = [
      (final: prev: {
        espeak = prev.espeak.override { mbrolaSupport = false; pcaudiolibSupport = false; sonicSupport = false; };
      })
    ];
  };
}
