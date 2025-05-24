#!/bin/bash

# This script can be used to format the python code with ruff.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run ruff as a pre-commit hook
run_as_precommit "ruff format --check" "$@"

# Run ruff
echo "Starting code formatting with ruff..." | print_info
ruff format "$@"

echo "✔ Code formatting finished" | print_success
