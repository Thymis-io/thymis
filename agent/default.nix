{ poetry2nix
, nix
, writeShellApplication
, python312
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-agent";
    projectDir = ./.;
    preferWheels = true;
    groups = [ ];
    checkGroups = [ "test" ];
    python = python312;
  }).dependencyEnv;
in
writeShellApplication {
  name = "thymis-agent";
  runtimeInputs = [ nix ];
  text = ''
    ${pythonEnv}/bin/uvicorn thymis_controller.main:app "$@"
  '';
}
