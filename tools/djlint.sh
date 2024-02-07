#!/bin/bash

# This script can be used to format the Django HTML templates with djlint.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run djlint
echo "Starting code formatting with djlint..." | print_info
# exclude invalid html files until this is resolved https://github.com/djlint/djLint/issues/703
djlint --reformat --quiet --lint "${PACKAGE_DIR}" --extend-exclude .djlintignore.html
echo "✔ Code formatting finished" | print_success
