{ poetry2nix
, writeShellApplication
, python313
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-agent";
    projectDir = ./.;
    preferWheels = true;
    checkGroups = [ "test" ];
    python = python313;
  }).dependencyEnv;
in
writeShellApplication {
  name = "thymis-agent";
  text = ''
    ${pythonEnv}/bin/thymis-agent
  '';
}
