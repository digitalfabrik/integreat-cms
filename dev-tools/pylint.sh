#!/bin/bash

# This script can be used to run the pylint_runner while ignoring migrations.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run pylint
echo "Starting code linting with pylint..." | print_info
pylint_runner
echo "✔ Linting finished" | print_success
