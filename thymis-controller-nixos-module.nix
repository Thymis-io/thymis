{ config, lib, pkgs, inputs, ... }:
let
  cfg = config.services.thymis-controller;
in
{
  options = {
    services.thymis-controller = {
      enable = lib.mkEnableOption "the Thymis controller";
      system-binfmt-aarch64-enable = lib.mkEnableOption "whether to enable the system binfmt for aarch64" // {
        default = if pkgs.stdenv.targetPlatform.system == "x86_64" then true else false;
      };
      system-binfmt-x86_64-enable = lib.mkEnableOption "whether to enable the system binfmt for x86_64";
      repo-path = lib.mkOption {
        type = lib.types.str;
        default = "/var/lib/thymis/repository";
        description = "Directory where the controller will store the repository holding the project";
      };
      database-url = lib.mkOption {
        type = lib.types.str;
        default = "sqlite:////var/lib/thymis/thymis.sqlite";
        description = "URL of the database";
      };
      base-url = lib.mkOption {
        type = lib.types.str;
        default = "http://localhost:8000";
        description = "Base URL of the controller, how it will be accessed from the outside";
      };
      auth-basic = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = "Whether to enable authentication using a basic username/password";
      };
      auth-basic-username = lib.mkOption {
        type = lib.types.str;
        default = "admin";
        description = "Username for basic authentication";
      };
      auth-basic-password-file = lib.mkOption {
        type = lib.types.path;
        default = "/var/lib/thymis/auth-basic-password";
        description = "File containing the password for basic authentication";
      };
      listen-host = lib.mkOption {
        type = lib.types.str;
        default = "127.0.0.1";
        description = "Host on which the controller listens for incoming connections";
      };
      listen-port = lib.mkOption {
        type = lib.types.int;
        default = 8000;
        description = "Port on which the controller listens for incoming connections";
      };
      nginx-vhost-enable = lib.mkEnableOption "whether to enable the Nginx virtual host";
      nginx-vhost-name = lib.mkOption {
        type = lib.types.str;
        default = "thymis";
        description = "Name of the Nginx virtual host";
      };
    };
  };
  config = lib.mkIf cfg.enable {
    systemd.services.thymis-controller = {
      description = "Thymis controller";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];
      script = "${inputs.thymis.packages.${config.nixpkgs.hostPlatform.system}.thymis-controller}/bin/thymis-controller";
      path = [
        "/run/current-system/sw"
        pkgs.git
        pkgs.nixpkgs-fmt
      ];
      environment = {
        THYMIS_REPO_PATH = cfg.repo-path;
        THYMIS_DATABASE_URL = cfg.database-url;
        THYMIS_BASE_URL = cfg.base-url;
        THYMIS_AUTH_BASIC = builtins.toString cfg.auth-basic;
        THYMIS_AUTH_BASIC_USERNAME = cfg.auth-basic-username;
        THYMIS_AUTH_BASIC_PASSWORD_FILE = cfg.auth-basic-password-file;
        UVICORN_HOST = cfg.listen-host;
        UVICORN_PORT = builtins.toString cfg.listen-port;
      };
    };
    services.nginx = lib.mkIf cfg.nginx-vhost-enable {
      enable = true;
      virtualHosts.${cfg.nginx-vhost-name} = {
        default = true;
        locations."/" = {
          proxyPass = "http://${cfg.listen-host}:${builtins.toString cfg.listen-port}";
          recommendedProxySettings = true;
          extraConfig = ''
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
          '';
        };
      };
      boot.binfmt.emulatedSystems = (lib.lists.optional cfg.system-binfmt-aarch64-enable "aarch64-linux")
        ++ (lib.lists.optional cfg.system-binfmt-x86_64-enable "x86_64-linux");
    };
  };
}
