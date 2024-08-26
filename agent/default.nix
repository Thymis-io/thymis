{ poetry2nix
, git
, nixpkgs-fmt
, nix
, writeShellApplication
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-agent";
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
  name = "thymis-agent";
  runtimeInputs = [ git nixpkgs-fmt nix ];
  text = ''
    ${pythonEnv}/bin/uvicorn thymis_controller.main:app "$@"
  '';
}
