#!/bin/bash

# This script can be used to lint the static files with eslint

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Run eslint as a pre-commit hook
run_as_precommit "npx eslint" "$@"

# Run prettier
echo "Starting code linting with eslint..." | print_info
npx eslint .
echo "✔ Linting finished" | print_success
