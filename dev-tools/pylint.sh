#!/bin/bash

# This script can be used to run the pylint_runner while ignoring migrations.

# Import utility functions
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Run pylint
echo "Starting code linting with pylint..." | print_info
pipenv run pylint_runner
echo "✔ Linting finished" | print_success
