{ buildNpmPackage
, runtimeShell
, nodejs
, lib
,
}:
buildNpmPackage {
  pname = "thymis-frontend";
  version = "0.0.1";
  src = ./.;
  npmDepsHash = "sha256-7tsGL+KypIKi4Dc0iHTLb67jcZzGk6t/sk4Qj4B14WI=";
  postInstall = ''
    mkdir -p $packageOut/build
    cp -r ./build/* $packageOut/build
    # create bin/thymis-frontend
    mkdir -p $out/bin
    cat > $out/bin/thymis-frontend <<EOF
    #!${runtimeShell}
    ${nodejs}/bin/node $packageOut/build/index.js
    EOF
    chmod +x $out/bin/thymis-frontend
  '';
}
