{ config, lib, pkgs, inputs, modulesPath, thymis-config, ... }:
let
  cfg = config.thymis.config;
  use-wifi = cfg.wifi-ssid != "" && cfg.wifi-password != "";
  # Define the settings format used for this program
  settingsFormat = pkgs.formats.json { };
in

{
  imports = [
    inputs.home-manager.nixosModules.default
    ./devices-module.nix
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
      networking.hostName = cfg.device-name;
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
      services.xserver.enable = true;
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
      users.users.nixos = {
        isNormalUser = true;
        createHome = true;
        password = cfg.password;
      };
      services.xserver.windowManager.i3.enable = true;
      services.xserver.windowManager.i3.configFile = pkgs.writeText "i3-config" ''
        # i3 config file (v4)
        bar mode invisible;
        exec ${pkgs.firefox}/bin/firefox --kiosk http://localhost:3000/kiosk
      '';
      networking.firewall = {
        allowedTCPPorts = [ 22 3000 ];
      };
      systemd.services.thymis-frontend = {
        description = "Thymis frontend";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-frontend}/bin/thymis-frontend";
        environment = {
          HOST = "127.0.0.1";
          PORT = "3000";
        };
      };
      systemd.services.thymis-controller = {
        description = "Thymis controller";
        after = [ "network.target" ];
        wantedBy = [ "multi-user.target" ];
        script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-controller}/bin/thymis-controller";
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
  ];
}
