#!/bin/bash

# This script can be used to format the python code with ruff.

# For the transitional phase we use both pylint and ruff.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Run ruff as a pre-commit hook
run_as_precommit "ruff check --force-exclude" "$@"

require_installed

# Run ruff
echo "Starting code linting and formatting with ruff..." | print_info
ruff check --fix "${BASE_DIR}"
# ruff format "${BASE_DIR}"
echo "✔ Code formatting finished" | print_success
