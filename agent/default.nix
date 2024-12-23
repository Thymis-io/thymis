{ poetry2nix
, writeShellApplication
, python312
,
}:
let
  pythonEnv = (poetry2nix.mkPoetryApplication {
    name = "thymis-agent";
    projectDir = ./.;
    preferWheels = true;
    checkGroups = [ "test" ];
    python = python312;
  }).dependencyEnv;
in
writeShellApplication {
  name = "thymis-agent";
  text = ''
    ${pythonEnv}/bin/thymis-agent
  '';
}
