{ poetry2nix
,
}:
poetry2nix.mkPoetryApplication {
  name = "thymis-controller";
  projectDir = ./.;
  preferWheels = true;
}
