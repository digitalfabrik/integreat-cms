#!/bin/bash

# This script executes the tests and starts the database docker container if necessary.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Delete outdated code coverage report
CODE_COVERAGE_DIR="${BASE_DIR:?}/htmlcov"
rm -rf "${CODE_COVERAGE_DIR}"

require_installed
require_database

# Set dummy key to enable SUMM.AI during testing
export INTEGREAT_CMS_SUMM_AI_API_KEY="dummy"

# If only particular tests should be run, test path can be passed as CLI argument
TEST_PATH=$1;

if [[ -z "$TEST_PATH" ]]; then
    echo -e "Running all tests..." | print_info
    deescalate_privileges pipenv run pytest --disable-warnings --quiet --numprocesses=auto --cov=integreat_cms --cov-report html
elif [[ -e "$TEST_PATH" ]]; then
    echo -e "Running tests in ${TEST_PATH}..." | print_info
    deescalate_privileges pipenv run pytest "$TEST_PATH" --quiet --disable-warnings --numprocesses=auto
else
    echo -e "${TEST_PATH}: No such file or directory" | print_error
    exit 1
fi

echo "✔ Tests successfully completed " | print_success

if [ -d "$CODE_COVERAGE_DIR" ]; then
    echo -e "Open the following file in your browser to view the test coverage:\n" | print_info
    echo -e "\tfile://${CODE_COVERAGE_DIR}/index.html\n" | print_bold
fi
