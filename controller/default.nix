{ poetry2nix
, git
, nixpkgs-fmt
, nix
, writeShellApplication
, thymis-frontend
, openssh
, python313
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-controller";
    projectDir = ./.;
    preferWheels = true;
    overrides = poetry2nix.overrides.withDefaults (final: prev: {
      fastapi-cli = python313.pkgs.fastapi-cli;
      bcrypt = python313.pkgs.bcrypt;
      http-network-relay = prev.http-network-relay.overridePythonAttrs (oldAttrs: {
        buildInputs = (oldAttrs.buildInputs or [ ]) ++ [ prev.poetry-core ];
      });
    });
    checkGroups = [ "test" ];
    python = python313;
  }).dependencyEnv;
in
writeShellApplication {
  name = "thymis-controller";
  runtimeInputs = [ git nixpkgs-fmt nix openssh ];
  text = ''
    export UVICORN_HOST="''${UVICORN_HOST:=127.0.0.1}"
    export UVICORN_PORT="''${UVICORN_PORT:=8000}"
    export THYMIS_FRONTEND_BINARY_PATH=${thymis-frontend}/bin/thymis-frontend
    export THYMIS_ALEMBIC_INI_PATH="''${THYMIS_ALEMBIC_INI_PATH:=${./alembic.ini}}"
    ${pythonEnv}/bin/uvicorn thymis_controller.main:app "$@"
  '';
}
