{
  poetry2nix,
  python3
}:
poetry2nix.mkPoetryApplication {
  name = "thymis-controller";
  projectDir = ./.;
}