#!/bin/bash

# This script checks if all dependencies in the lock files are up to date and increments the version numbers if necessary.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

ensure_not_root

# Check if npm dependencies are up to date
echo "Updating JavaScript dependencies..." | print_info
npx npm-check --update-all --skip-unused

# Check if pip dependencies are up to date
echo "Updating Python dependencies..." | print_info
pipenv update --dev
