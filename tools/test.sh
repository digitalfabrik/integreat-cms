#!/bin/bash

# This script executes the tests and starts the database docker container if necessary.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Delete outdated code coverage report
CODE_COVERAGE_DIR="${BASE_DIR:?}/htmlcov"
rm -rf "${CODE_COVERAGE_DIR}"

require_installed
require_database

# Set dummy key to enable SUMM.AI during testing
export INTEGREAT_CMS_SUMM_AI_API_KEY="dummy"

# Set dummy key to enable DeepL during testing
export INTEGREAT_CMS_DEEPL_AUTH_KEY="dummy"

# Set dummy key to enable Textlab during testing
export INTEGREAT_CMS_TEXTLAB_API_KEY="dummy"

# Disable linkcheck listeners during testing
export INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS=1

# Disable background tasks during testing
export INTEGREAT_CMS_BACKGROUND_TASKS_ENABLED=0

TESTS=()

# Parse given command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        # If only tests affected by recent changed should be run, --changed can be passed as a flag
        --changed) CHANGED=1;shift;;
        # Verbosity for pytest
        -v|-vv|-vvv|-vvvv) VERBOSITY="$1";shift;;
        # Select tests by keyword expression
        -k) shift;KW_EXPR="$1";shift;;
        # Select tests by marker
        -m) shift;MARKER="$1";shift;;
        # If only particular tests should be run, test path can be passed as CLI argument
        *) TESTS+=("$1");shift;;
    esac
done

# The default pytests args we use
PYTEST_ARGS=("--disable-warnings" "--color=yes")

if [[ -n "${VERBOSITY}" ]]; then
    PYTEST_ARGS+=("$VERBOSITY")
else
    PYTEST_ARGS+=("--quiet" "--numprocesses=auto")
fi

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
        unset TESTS
        # Tell testmon to run all tests and collect data
        PYTEST_ARGS+=("--testmon-noselect")
    fi
else
    # Run all tests, but update list of tests
    PYTEST_ARGS+=("--testmon-noselect")
fi

# Determine whether coverage data should be collected
if [[ -z "${CHANGED}" ]] && (( ${#TESTS[@]} == 0 )); then
    PYTEST_ARGS+=("--cov=integreat_cms" "--cov-report=html")
fi

if [[ -n "${KW_EXPR}" ]] || [[ -n "${MARKER}" ]] || (( ${#TESTS[@]} )); then
    MESSAGES=()
    if [[ -n "${KW_EXPR}" ]]; then
        MESSAGES+=("\"${KW_EXPR}\"")
        PYTEST_ARGS+=("-k" "${KW_EXPR}")
    fi
    if [[ -n "${MARKER}" ]]; then
        MESSAGES+=("with ${MARKER}")
        PYTEST_ARGS+=("-m" "${KW_EXPR}")
    fi
    # Check whether test paths exist
    for t in "${TESTS[@]}"; do
        if [[ -e "${t%%::*}" ]]; then
            # Adapt message and append to pytest arguments
            MESSAGES+=("${t}")
            PYTEST_ARGS+=("${t}")
        elif [[ -n "${t}" ]]; then
            # If the test path does not exist but was non-zero, show an error
            echo -e "${t%%::*}: No such file or directory" | print_error
            exit 1
        fi
    done
    TEST_MESSAGE=$(join_by ", " "${MESSAGES[@]}")
    TEST_MESSAGE=" in ${TEST_MESSAGE}"
fi

echo -e "Running all tests${TEST_MESSAGE}${CHANGED_MESSAGE}..." | print_info
deescalate_privileges pytest "${PYTEST_ARGS[@]}"
echo "✔ Tests successfully completed " | print_success

if [[ -d "${CODE_COVERAGE_DIR}" ]]; then
    echo -e "Open the following file in your browser to view the test coverage:\n" | print_info
    echo -e "\tfile://${CODE_COVERAGE_DIR}/index.html\n" | print_bold
fi
