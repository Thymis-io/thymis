{ poetry2nix
, writeShellApplication
, python313
, shadow
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-agent";
    projectDir = ./.;
    preferWheels = true;
    checkGroups = [ "test" ];
    python = python313;
    overrides = poetry2nix.overrides.withDefaults (final: prev: {
      http-network-relay = prev.http-network-relay.overridePythonAttrs (oldAttrs: {
        buildInputs = (oldAttrs.buildInputs or [ ]) ++ [ prev.poetry-core ];
      });
    });
  }).dependencyEnv;
in
writeShellApplication {
  name = "thymis-agent";
  runtimeInputs = [ shadow ];
  text = ''
    exec ${pythonEnv}/bin/thymis-agent "$@"
  '';
}
