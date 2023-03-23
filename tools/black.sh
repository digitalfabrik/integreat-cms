#!/bin/bash

# This script can be used to format the python code according to the black code style.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Run black
echo "Starting code formatting with black..." | print_info
black "${BASE_DIR}"
echo "✔ Code formatting finished" | print_success
