#!/bin/bash

# This script checks if all dependencies in the lock files are up to date and increments the version numbers if necessary.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Check if npm dependencies are up to date
echo "Updating JavaScript dependencies..." | print_info
npx npm-check --update-all --skip-unused

# Fix npm security issues (skip all breaking changes)
echo "Running security audit of JavaScript dependencies..." | print_info
npm audit fix || true

# Check if pip dependencies are up to date
echo "Updating Python dependencies..." | print_info
pipenv update --dev
