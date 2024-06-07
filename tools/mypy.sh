#!/bin/bash

# This script can be used to check the python type annotations with my[py].

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run mypy as a pre-commit hook
run_as_precommit "mypy --scripts-are-modules" "$@"

# Run my[py]
echo "Starting type checking with my[py]..." | print_info
export FORCE_COLOR=1
mypy  --scripts-are-modules "${BASE_DIR}" | sort
echo "✔ Type checking finished" | print_success
