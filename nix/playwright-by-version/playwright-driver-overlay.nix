nixpkgs: final: prev:
let
  inherit (prev.stdenv.hostPlatform) system;
  inherit (prev) lib makeFontsConf linkFarm throwSystem cacert;
  # otherVersion = "1.50.0";
  # otherHash = "sha256-5ktir561kbhzA0IJ/X7pzGT2Rcejx4bVypowYe+O1Xc=";
  playwrightVersions = lib.importJSON ./playwright-versions.json;
  build-driver = otherVersion: otherHash:
    let
      finalPlaywright = final.playwright-driver-by-version."${otherVersion}";
      suffix =
        {
          x86_64-linux = "linux";
          aarch64-linux = "linux-arm64";
          x86_64-darwin = "mac";
          aarch64-darwin = "mac-arm64";
        }.${system} or throwSystem;
      browsers-linux = lib.makeOverridable (
        { withChromium ? true
        , withFirefox ? true
        , withWebkit ? true
        , withFfmpeg ? true
        , fontconfig_file ? makeFontsConf {
            fontDirectories = [ ];
          }
        }:
        let
          browsers =
            lib.optionals withChromium [ "chromium" ]
            ++ lib.optionals withFirefox [ "firefox" ]
            ++ lib.optionals withWebkit [ "webkit" ]
            ++ lib.optionals withFfmpeg [ "ffmpeg" ];
        in
        linkFarm "playwright-browsers" (
          lib.listToAttrs (
            map
              (
                name:
                let
                  value = finalPlaywright.passthru.browsersJSON.${name};
                in
                lib.nameValuePair
                  # TODO check platform for revisionOverrides
                  "${name}-${value.revision}"
                  (
                    prev.callPackage ("${nixpkgs}/pkgs/development/web/playwright/${name}.nix") (
                      {
                        inherit suffix system throwSystem;
                        inherit (value) revision;
                      }
                      // lib.optionalAttrs (name == "chromium") {
                        inherit fontconfig_file;
                      }
                    )
                  )
              )
              browsers
          )
        )
      );
      browsers-mac = prev.stdenv.mkDerivation {
        pname = "playwright-browsers";
        version = otherVersion;

        dontUnpack = true;

        nativeBuildInputs = [ cacert ];

        installPhase = ''
          runHook preInstall

          export PLAYWRIGHT_BROWSERS_PATH=$out
          ${finalPlaywright}/cli.js install
          rm -r $out/.links

          runHook postInstall
        '';

        meta.platforms = lib.platforms.darwin;
      };
      playwright-driver = (prev.playwright-driver.overrideAttrs (oldAttrs: {
        version = "${otherVersion}";
        src = prev.fetchFromGitHub {
          owner = "microsoft";
          repo = "playwright";
          rev = "v${otherVersion}";
          hash = otherHash;
        };
        passthru = {
          browsersJSON = (lib.importJSON ./browsers.${otherVersion}.json).browsers;
          browsers =
            {
              x86_64-linux = browsers-linux { };
              aarch64-linux = browsers-linux { };
              x86_64-darwin = browsers-mac;
              aarch64-darwin = browsers-mac;
            }.${system} or throwSystem;
          browsers-chromium = browsers-linux { };
        };
      }));
    in
    playwright-driver;
in
{
  playwright-driver-by-version = (
    builtins.mapAttrs
      (
        otherVersion: otherHash:
          build-driver otherVersion otherHash
      )
      playwrightVersions
  ) //
  {
    "${prev.playwright-driver.version}" = prev.playwright-driver;
  };
}
