#!/bin/bash

# This script executes the tests and starts the database docker container if necessary.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_database

deescalate_privileges pipenv run integreat-cms-cli test cms
echo "✔ Tests successfully completed " | print_success
