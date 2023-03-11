#!/bin/bash

# This script checks if all dependencies in the lock files are up to date and increments the version numbers if necessary.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Check if npm dependencies are up to date
echo "Updating JavaScript dependencies..." | print_info
npm update

# Fix npm security issues (skip all breaking changes)
echo "Running security audit of JavaScript dependencies..." | print_info
npm audit fix || true

# Update pip dependencies
echo "Updating Python dependencies..." | print_info
# Create temporary venv to make sure dev dependencies are not included
python3 -m venv .venv.tmp
source .venv.tmp/bin/activate
# Install package locally (without the pinned extra, so the newest available versions are installed)
pip install -e .
# Parse the newly installed versions
NEW_VERSIONS=$(pip freeze --exclude-editable --local | sort | sed  --regexp-extended 's/^(.*)$/    "\1",\\n/g' | tr -d '\n')
# Write the new versions to pyproject.toml
sed --in-place --regexp-extended "/^pinned = \[$/,/^\]$/c\pinned = [\n${NEW_VERSIONS}]" pyproject.toml
# Remove the temporary venv
deactivate
rm -rf .venv.tmp

# Install updated versions in the real venv
bash "${DEV_TOOL_DIR}/install.sh"
