{ config, lib, pkgs, inputs, modulesPath, ... }:
let
  cfg = config.services.thymis-controller;
in

{
  imports = [
  ];
  options = {
    services.thymis-controller = {
      enable = lib.mkEnableOption "the Thymis controller";
      repo-dir = lib.mkOption {
        type = lib.types.str;
        default = "/var/lib/thymis";
        description = "Directory where the controller will store its state";
      };
    };
  };
  config = lib.mkIf cfg.enable {
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
        REPO_PATH = cfg.repo-dir;
      };
    };
    services.nginx = {
      enable = true;
      virtualHosts.default = {
        default = true;
        locations."/" = {
          proxyPass = "http://localhost:8000";
          recommendedProxySettings = true;
          extraConfig = ''
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
          '';
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
  };
}
