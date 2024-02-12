{ buildNpmPackage
, runtimeShell
, nodejs
}:
buildNpmPackage {
  pname = "thymis-frontend";
  version = "0.0.1";
  src = ./.;
  npmDepsHash = "sha256-s6CXq1Ff1fB+0dStq1DbeZFjWuGgmPTp4TQFJ/5r1m4=";
  postInstall = ''
    mkdir -p $packageOut/build
    cp -r ./build/* $packageOut/build
    # create bin/thymis-frontend
    mkdir -p $out/bin
    cat > $out/bin/thymis-frontend <<EOF
    #!${runtimeShell}
    ${nodejs}/bin/node -r dotenv/config $packageOut/build/index.js
    EOF
    chmod +x $out/bin/thymis-frontend
  '';
}
