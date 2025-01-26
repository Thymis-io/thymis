#!/usr/bin/env bash

# called with a playwright version in $1

set -euo pipefail

# DRIVER_VERSION=$1
DRIVER_VERSION=${1:-""}
if [ -z "$DRIVER_VERSION" ]; then
    echo "Usage: $0 <playwright-version>"
    exit 1
fi
root="$(dirname "$(readlink -f "$0")")"


curl -fsSl \
    "https://raw.githubusercontent.com/microsoft/playwright/v$DRIVER_VERSION/packages/playwright-core/browsers.json" \
    | jq '
      .comment = "This file is kept up to date via update.sh"
      | .browsers |= (
        [.[]
          | select(.installByDefault) | del(.installByDefault)]
          | map({(.name): . | del(.name)})
          | add
      )
    ' > "$root/browsers.$DRIVER_VERSION.json"

git add "$root/browsers.$DRIVER_VERSION.json"

# add version with hash "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" into playwright-versions.json
# then build nix build .#playwright-driver-all
# look at the output and replace the hash with the actual hash
# then commit the change

if grep -q "\"$DRIVER_VERSION\"" "$root/playwright-versions.json"; then
    echo "Version $DRIVER_VERSION already exists in playwright-versions.json"
else
    echo "Adding version $DRIVER_VERSION to playwright-versions.json"
    jq --arg version "$DRIVER_VERSION" --arg hash "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" '
        .[$version] = $hash
    ' "$root/playwright-versions.json" > "$root/playwright-versions.json.tmp"
    mv "$root/playwright-versions.json.tmp" "$root/playwright-versions.json"
    git add "$root/playwright-versions.json"

    echo "Now run nix build .#playwright-driver-all and update the hash in playwright-versions.json"
    nix build .#playwright-driver-all --show-trace --print-build-logs 2>&1 | tee build.log || true
    newHash=$(grep -oP 'got:    sha256-\K[0-9a-zA-Z/+=]+' build.log)
    rm build.log

    jq --arg version "$DRIVER_VERSION" --arg hash "$newHash" '
        .[$version] = $hash
    ' "$root/playwright-versions.json" > "$root/playwright-versions.json.tmp"
    mv "$root/playwright-versions.json.tmp" "$root/playwright-versions.json"
    git add "$root/playwright-versions.json"
fi
