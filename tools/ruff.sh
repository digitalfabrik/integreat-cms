#!/bin/bash

# This script can be used to format the python code with ruff.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run ruff as a pre-commit hook
run_as_precommit "ruff check" "$@"
run_as_precommit "ruff format --check" "$@"

# Run ruff
echo "Starting code linting and formatting with ruff..." | print_info
ruff check --fix "${BASE_DIR}" || true
ruff format "${BASE_DIR}"

echo "✔ Code formatting & linting finished" | print_success
