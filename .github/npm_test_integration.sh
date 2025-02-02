#!/usr/bin/env bash
OUR_NIX=$(readlink -f $(which nix))
OUR_NIX_PARENT=$(dirname $OUR_NIX)
TEE=$(which tee)
OLD_PATH=$PATH
export PATH=$OUR_NIX_PARENT
$OUR_NIX develop .#forNpmTesting --command npm run test:integration "$@" 2>&1 | $TEE output.log
export PATH=$OLD_PATH
PLAYWRIGHT_EXIT_CODE=$?
if grep -q -e "Error: A snapshot doesn't exist at" -e "Screenshot comparison failed" output.log; then
    echo "Playwright tests failed due to a snapshot issue"
    echo "SNAPSHOT_DIFFERENCES=true" >> $GITHUB_ENV
fi
if grep -q -E -e "npx playwright install" -e "error: attribute '\"[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+\"' missing" output.log; then
    echo "Playwright tests failed due to missing browsers"
    echo "MISSING_BROWSERS=true" >> $GITHUB_ENV
fi
if grep -q -E -e "[[:digit:]]+ failed" -e "was not able to start" output.log; then
    echo "Playwright tests failed"
    exit 1
fi
exit $PLAYWRIGHT_EXIT_CODE
