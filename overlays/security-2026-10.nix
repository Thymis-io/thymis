# October 2026 security overlay for the Thymis flake — the gaps the pinned nixos-26.05
# (da6dc0e7b260, 2026-10-21) does not carry yet.
#
# The pin already supplies: linux 6.18.57, nginx 1.30.6, openssl 3.6.5, systemd 260.5,
# nodejs_22 22.23.4, nodejs_26 26.12.1, php 8.4.27, the default NixOS CA blacklist
# (emSign x3 + Comodo AAA) and docker 29.9.1 (with containerd v2.4.2 bundled).  Overlaying
# any of those here would only rebuild them locally for nothing.
#
# What is still vulnerable at every available channel (nixos-26.05, nixos-unstable and
# master) and is closed here:
#   brotli 1.2.0        CVE-2026-111497 (decoder OOB write, every libbrotlidec consumer)
#   curl 8.22.0         CVE-2026-92392 + 21 further fixes in 8.23.0
#   c-ares 1.34.8       GHSA-fqh5-3x7m-wp44, GHSA-wpr3-8q3r-4q8c
#   nodejs_24 24.21.0   the 2026-10-21 node release (22.23.4 / 24.22.1 / 26.12.1) — the
#                       26.05 pin fixes the 22 and 26 lines but leaves 24 at 24.21.0 and
#                       on the unpatched shared brotli
#   bun 1.3.13          bundles its own brotli decoder; 1.4.4 is the first fixed release
#
# openssh 10.6p1 (nine CVEs) is deliberately NOT here: a hand `overrideAttrs` to 10.6 does
# not build.  It is wired as `services.openssh.package` from the `nixpkgs-unstable` input
# (cache-backed at 02c087f3fe67) in `flake.nix`.
#
# docker / podman are deliberately NOT here: this repo only uses `pkgs.dockerTools` to
# *build* images (nix/docker.nix), no container runtime runs in any closure, so there is no
# Go toolchain to rebuild for CVE-2026-111943.
final: prev:
let
  # nixpkgs builds node with `--shared-brotli`, i.e. node resolves BrotliDecoder* from the
  # system brotli.  The brotli override below already fixes that, but the node version bump
  # is still needed for the rest of the 2026-10-21 release — and node 22.23.4 / 24.22.1 /
  # 26.12.1 ship the patched decoder in deps/brotli anyway, so drop the shared-library flag
  # and let each node line end up with exactly one patched decoder.
  bumpNode =
    pkg: version: sha256:
    pkg.overrideAttrs (old: {
      inherit version;
      src = final.fetchurl {
        url = "https://nodejs.org/dist/v${version}/node-v${version}.tar.xz";
        inherit sha256;
      };
      configureFlags = builtins.filter
        (
          f: !(prev.lib.hasPrefix "--shared-brotli" (toString f))
        )
        old.configureFlags;
      buildInputs = builtins.filter (x: (x.pname or "") != "brotli") old.buildInputs;
    });

  nodejs-slim_22 = bumpNode prev.nodejs-slim_22 "22.23.4" "1sfam916q570pdp9algf1hjjwmcj4bg4cv6rcfla5l0jss1dr6kv";
  nodejs-slim_24 = bumpNode prev.nodejs-slim_24 "24.22.1" "0caj8cxrd78sr6lbb0zsgpxw8v51nq2gsn7kqaqaxkc0c9wpjlsg";
  nodejs-slim_26 = bumpNode prev.nodejs-slim_26 "26.12.1" "136kvg0pi6b41h86haf7f7hlw77ckkx9gvwr7zcxidjrd0lkngh5";

  # Only `curl` and `curlFull` are re-pointed at 8.23.0 and only version+src change
  # (nixpkgs applies no patches to curl).  `curlMinimal` is deliberately left on 8.22.0:
  # cmake links it, so bumping it would invalidate cmake and a large part of the tree.
  # Hash: `nix hash file --type sha256 --sri curl-8.23.0.tar.xz`.
  bumpCurl =
    pkg: pkg.overrideAttrs (old: {
      version = "8.23.0";
      src = final.fetchurl {
        urls = [
          "https://curl.se/download/curl-8.23.0.tar.xz"
          "https://github.com/curl/curl/releases/download/curl-8_23_0/curl-8.23.0.tar.xz"
        ];
        hash = "sha256-ja3X0lNqMU+YKtBaZRtxP0Jr99Aswsds/7l5byIY5sU=";
      };
    });
in
{
  inherit nodejs-slim_22 nodejs-slim_24 nodejs-slim_26;

  # all-packages binds the plain attributes to the pre-overlay derivations, so re-point
  # them at the bumped slims instead of leaving them on the vulnerable builds.
  nodejs_22 = prev.nodejs_22.override { nodejs-slim = nodejs-slim_22; };
  nodejs_24 = prev.nodejs_24.override { nodejs-slim = nodejs-slim_24; };
  nodejs_26 = prev.nodejs_26.override { nodejs-slim = nodejs-slim_26; };
  nodejs = final.nodejs_24;
  nodejs-slim = final.nodejs-slim_24;

  # The decoder bug is in google/brotli itself, so this one entry fixes every
  # libbrotlidec consumer at once: curl (and through it git-minimal), the C library,
  # python3Packages.brotli (it does `inherit (brotli) version src`) and brotlicffi
  # (built with USE_SHARED_BROTLI=1 against the C package).  Same src hash as the
  # nixpkgs staging bump (PR #577208).
  #
  # `dontPatch`/`patches` are required here, not cosmetic: nixpkgs' nodejs.nix wraps the
  # `brotli` attribute with a patch carrying upstream 0ed4268a (the CVE-2026-111497 fix) for
  # every node line except 24 (pkgs/development/web/nodejs/nodejs.nix:154-166), and that
  # commit is already in the 1.2.1 tarball — re-applying it aborts with "Reversed (or
  # previously applied) patch detected" and takes node 20/22/26 plus everything downstream
  # (system-units, etc.drv, the toplevel) with it.  The pin's own patch entry (e230f474) is a
  # LoongArch64/IA64 build fix our platforms do not need, so skipping the patch phase
  # entirely is the correct form.  Same shape as elikoga-nixos and udysseus/thymis/servers.
  brotli = prev.brotli.overrideAttrs (old: {
    version = "1.2.1";
    dontPatch = true;
    patches = [ ];
    src = final.fetchFromGitHub {
      owner = "google";
      repo = "brotli";
      tag = "v1.2.1";
      hash = "sha256-llY72cYffDv0ugsH0p89xIPEbElV4L8u7U/Fe8hT3gI=";
    };
  });

  # CVE-2026-92392 + the rest of curl 8.23.0 — see `bumpCurl` above.
  curl = bumpCurl prev.curl;
  curlFull = bumpCurl prev.curlFull;

  # c-ares: node builds with `--shared-cares`, so this rides the node rebuild too.
  c-ares = prev.c-ares.overrideAttrs (old: {
    version = "1.34.9";
    src = final.fetchurl {
      url = "https://github.com/c-ares/c-ares/releases/download/v1.34.9/c-ares-1.34.9.tar.gz";
      hash = "sha256-k2S3ChLrWaBoMPtIjZNX+QEA3/DZiyPqNZOhg9Q+by8=";
    };
  });

  # bun bundles its own brotli copy.  No nixpkgs revision carries 1.4.4 yet (verified:
  # nixos-unstable is still 1.3.13).  Asset digests are the upstream GitHub release assets,
  # converted with `nix hash convert --to sri --hash-algo sha256`.  Nothing in this flake
  # references bun today, so the four sources stay unfetched (they are lazy FODs).
  bun = prev.bun.overrideAttrs (old: {
    version = "1.4.4";
    # bun takes its source from passthru.sources, not `src`; silence the
    # "version overridden without src" warning.
    __intentionallyOverridingVersion = true;
    passthru =
      old.passthru
      // {
        sources = {
          "aarch64-darwin" = final.fetchurl {
            url = "https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-darwin-aarch64.zip";
            hash = "sha256-wkDX8My5DCY6hJ/NsJt+5iYw2SE0jtaq/ahrnVd7xRA=";
          };
          "aarch64-linux" = final.fetchurl {
            url = "https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-linux-aarch64.zip";
            hash = "sha256-uqa7NvUdblhWHgK76oJQOKnfRU9nPW13bou/hvjHhQ4=";
          };
          "x86_64-darwin" = final.fetchurl {
            url = "https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-darwin-x64-baseline.zip";
            hash = "sha256-1KFVrfv9CRVes7oFyeOlRPOSl9emhhbTx3WfZ6tcR9w=";
          };
          "x86_64-linux" = final.fetchurl {
            url = "https://github.com/oven-sh/bun/releases/download/bun-v1.4.4/bun-linux-x64.zip";
            hash = "sha256-v4zL+ysLgBWeD5ptFcVTF63YB3U028YTCj7bUvzLOVw=";
          };
        };
      };
  });
}
