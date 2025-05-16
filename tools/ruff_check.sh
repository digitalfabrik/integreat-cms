#!/bin/bash

# This script can be used to lint the python code with ruff.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run ruff as a pre-commit hook
run_as_precommit "ruff check" "$@"

# Run ruff
echo "Starting code linting with ruff..." | print_info
ruff check --fix "$@" || true

echo "✔ Code linting finished" | print_success
