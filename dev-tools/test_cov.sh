#!/bin/bash

# This script executes the tests and starts the database docker container if necessary.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Delete outdated code coverage
rm -rf "${BASE_DIR:?}/htmlcov/"

require_installed
require_database

deescalate_privileges pipenv run integreat-cms-cli test tests --set=COVERAGE --verbosity "${SCRIPT_VERBOSITY}"
echo "✔ Tests successfully completed " | print_success
echo -e "Open the following file in your browser to view the test coverage:\n" | print_info
echo -e "\tfile://${BASE_DIR}/htmlcov/index.html\n" | print_bold
