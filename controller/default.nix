{ poetry2nix
, git
, nixpkgs-fmt
, nix
, writeShellApplication
, thymis-frontend
, python313
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-controller";
    projectDir = ./.;
    preferWheels = true;
    overrides = poetry2nix.overrides.withDefaults (self: super: {
      fastapi-cli = python313.pkgs.fastapi-cli;
      bcrypt = python313.pkgs.bcrypt;
    });
    checkGroups = [ "test" ];
    python = python313;
  }).dependencyEnv;
in
writeShellApplication {
  name = "thymis-controller";
  runtimeInputs = [ git nixpkgs-fmt nix ];
  text = ''
    export UVICORN_HOST="''${UVICORN_HOST:=127.0.0.1}"
    export UVICORN_PORT="''${UVICORN_PORT:=8000}"
    export THYMIS_FRONTEND_BINARY_PATH=${thymis-frontend}/bin/thymis-frontend
    export THYMIS_ALEMBIC_INI_PATH="''${THYMIS_ALEMBIC_INI_PATH:=${./alembic.ini}}"
    ${pythonEnv}/bin/uvicorn thymis_controller.main:app "$@"
  '';
}
