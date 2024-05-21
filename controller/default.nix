{ poetry2nix
, git
, nixpkgs-fmt
, makeWrapper
, lib
,
}:
poetry2nix.mkPoetryApplication {
  name = "thymis-controller";
  projectDir = ./.;
  preferWheels = true;
  overrides = poetry2nix.overrides.withDefaults (self: super: {
    thymis-enterprise = null;
  });
  nativeBuildInputs = [ makeWrapper ];
  postInstall = ''
    wrapProgram $out/bin/thymis-controller \
      --prefix PATH : ${lib.makeBinPath [ git nixpkgs-fmt ]}
  '';
}
