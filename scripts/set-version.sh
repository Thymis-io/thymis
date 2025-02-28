#!/usr/bin/env bash

set -e

# This script sets the version of the project in agent/pyproject.toml, controller/pyproject.toml, frontend/package.json
# and runs `poetry lock` `poetry install`, `npm install` respectively.

MY_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="$(dirname "$MY_DIR")"

# if "--no-dev-version" is passed, then the version will not have .dev, or -dev appended to it.
NO_DEV_VERSION=false
VERSION=""

for arg in "$@"
do
    if [ "$arg" == "--no-dev-version" ]; then
        NO_DEV_VERSION=true
    else
        VERSION=$arg
    fi
done

# Check if version is passed correctly (matches the regex)
VERSION_REGEX="^([0-9]+)\.([0-9]+)\.([0-9]+)$"
if [[ ! $VERSION =~ $VERSION_REGEX ]]; then
    echo "Invalid version. Please pass a version in the format x.y.z"
    exit 1
fi

# Get the version from the args

if [ "$NO_DEV_VERSION" = true ]; then
    PY_VERSION=$VERSION
    NPM_VERSION=$VERSION
else
    PY_VERSION=$VERSION.dev
    NPM_VERSION=$VERSION-dev
fi

# Set the version in agent/pyproject.toml
sed -i "s/^version = .*/version = \"$PY_VERSION\"/" $PROJECT_DIR/agent/pyproject.toml

# run poetry lock and install
(cd $PROJECT_DIR/agent && poetry lock)

# Set the version in controller/pyproject.toml
sed -i "s/^version = .*/version = \"$PY_VERSION\"/" $PROJECT_DIR/controller/pyproject.toml

# run poetry lock and install
(cd $PROJECT_DIR/controller && poetry lock)

# Set the version in frontend/package.json
sed -i "s/\"version\": .*/\"version\": \"$NPM_VERSION\",/" $PROJECT_DIR/frontend/package.json

# run npm install
(cd $PROJECT_DIR/frontend && rm -rf node_modules && npm install)
