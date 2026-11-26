#!/bin/bash

# This script updates the locked dependency versions and installs them in the local environment.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Parse command line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    --package) PACKAGE="$2"; shift 2;;
    --package=*) PACKAGE="${1#*=}"; shift 1;;
    *) echo "Unknown option: $1" | print_error; exit 1;;
  esac
done

# Check if npm dependencies are up to date
echo "Updating JavaScript dependencies..." | print_info
npm update

# Fix npm security issues (skip all breaking changes)
echo "Running security audit of JavaScript dependencies..." | print_info
npm audit fix || true

# Update the locked Python dependencies
if [[ -n "${PACKAGE}" ]]; then
    echo "Updating the Python dependency ${PACKAGE}..." | print_info
    uv lock --upgrade-package "${PACKAGE}"
else
    echo "Updating all Python dependencies..." | print_info
    uv lock --upgrade
fi

# Install the updated versions
uv sync --locked

echo "✔ Updated uv.lock and installed the new versions" | print_success
