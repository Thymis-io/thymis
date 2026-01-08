#!/usr/bin/env bash
set -euo pipefail
OUR_NIX=$(readlink -f $(which nix))
OUR_NIX_PARENT=$(dirname $OUR_NIX)
TEE=$(which tee)
PYTHON=$(which python)
OLD_PATH=$PATH
export PATH=$OUR_NIX_PARENT
UVICORN_PORT=$($PYTHON -c 'import socket; s=socket.socket(); s.bind(("", 0)); print(s.getsockname()[1]); s.close()')
UVICORN_PORT=$UVICORN_PORT $OUR_NIX develop .#forNpmTesting --command npm run test:integration "$@" 2>&1 | $TEE output.log
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
if tail -n 25 output.log | grep -q -E -e "[[:digit:]]+ failed" -e "was not able to start" -e "Application startup failed" -e "Error: Timed out waiting [[:digit:]]+ms from config.webServer"; then
    echo "Playwright tests failed"
    exit 1
fi
exit $PLAYWRIGHT_EXIT_CODE
