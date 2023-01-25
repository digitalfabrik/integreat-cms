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

# Disable linkcheck listeners during testing
export INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS=1

# Parse given command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        # If only tests affected by recent changed should be run, --changed can be passed as a flag
        --changed) CHANGED=1;shift;;
        # If only particular tests should be run, test path can be passed as CLI argument
        *) TEST_PATH=$1;shift;;
    esac
done

# The default pytests args we use
PYTEST_ARGS=("--quiet" "--disable-warnings" "--numprocesses=auto")

# Check if --changed flag was passed
if [[ -n "${CHANGED}" ]]; then
    # Check if .testmondata file exists
    if [[ -f ".testmondata" ]]; then
        # Only run changed tests and don't update dependency database
        PYTEST_ARGS+=("--testmon-nocollect")
        CHANGED_MESSAGE=" affected by recent changes"
    else
        # Inform that all tests will be run
        echo -e "\nIt looks like you have not run pytest without the \"--changed\" flag before." | print_warning
        echo -e "Pytest has to build a dependency database by running all tests without the flag once.\n" | print_warning
        # Override test path argument
        unset TEST_PATH
        # Tell testmon to run all tests and collect data
        PYTEST_ARGS+=("--testmon-noselect")
    fi
else
    # Run all tests, but update list of tests
    PYTEST_ARGS+=("--testmon-noselect")
fi

# Determine whether coverage data should be collected
if [[ -z "${CHANGED}" && -z "${TEST_PATH}" ]]; then
    PYTEST_ARGS+=("--cov=integreat_cms" "--cov-report=html")
fi

# Check whether test path exists
if [[ -e "${TEST_PATH}" ]]; then
    # Adapt message and append to pytest arguments
    TEST_MESSAGE=" in ${TEST_PATH}"
    PYTEST_ARGS+=("${TEST_PATH}")
elif [[ -n "${TEST_PATH}" ]]; then
    # If the test path does not exist but was non-zero, show an error
    echo -e "${TEST_PATH}: No such file or directory" | print_error
    exit 1
fi

echo -e "Running all tests${TEST_MESSAGE}${CHANGED_MESSAGE}..." | print_info
deescalate_privileges pytest "${PYTEST_ARGS[@]}"
echo "✔ Tests successfully completed " | print_success

if [[ -d "${CODE_COVERAGE_DIR}" ]]; then
    echo -e "Open the following file in your browser to view the test coverage:\n" | print_info
    echo -e "\tfile://${CODE_COVERAGE_DIR}/index.html\n" | print_bold
fi
