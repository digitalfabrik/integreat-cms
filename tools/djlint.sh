#!/bin/bash

# This script can be used to format the Django HTML templates with djlint.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run djlint as a pre-commit hook
run_as_precommit "djlint --profile=django -e=html --reformat --quiet --lint" "$@"

# Run djlint
echo "Starting code formatting with djlint..." | print_info
djlint --reformat --quiet --lint "${PACKAGE_DIR}"
echo "✔ Code formatting finished" | print_success
