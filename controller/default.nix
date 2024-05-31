{ poetry2nix
, git
, nixpkgs-fmt
, nix
, writeShellApplication
, thymis-frontend
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-controller";
    projectDir = ./.;
    preferWheels = true;
    overrides = poetry2nix.overrides.withDefaults (self: super: {
      thymis-enterprise = null;
    });
    groups = [ ];
    checkGroups = [ "test" ];
  }).dependencyEnv;
  # in pythonEnv
in
writeShellApplication {
  name = "thymis-controller";
  runtimeInputs = [ git nixpkgs-fmt nix ];
  text = ''
    export FRONTEND_BINARY=${thymis-frontend}/bin/thymis-frontend
    export UVICORN_HOST=0.0.0.0
    export UVICORN_PORT=8000
    ${pythonEnv}/bin/uvicorn thymis_controller.main:app "$@"
  '';
}
