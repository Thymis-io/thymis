{ poetry2nix
,
}:
poetry2nix.mkPoetryApplication {
  name = "thymis-controller";
  projectDir = ./.;
  preferWheels = true;
  overrides = poetry2nix.overrides.withDefaults (self: super: {
    thymis-enterprise = null;
  });
}
