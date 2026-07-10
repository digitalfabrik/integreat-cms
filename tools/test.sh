#!/bin/bash

# This script executes the tests.
#
# By default the suite runs inside a Docker container that mirrors the CircleCI
# environment (see docker-compose.test.yml), so a local run matches CI by
# construction. Use --local to run on the host instead (starting the database
# docker container if necessary).
#
# Usage examples:
#   ./tools/test.sh                          Run the full test suite (in Docker)
#   ./tools/test.sh --local                  Run the full test suite on the host
#   ./tools/test.sh -m unit                  Run only unit tests (no database, fast)
#   ./tools/test.sh -m "not slow"            Skip slow parametrized view tests
#   ./tools/test.sh -m "not slow and not unit"  Integration tests only
#   ./tools/test.sh -v -k test_tree_mutex    Run a specific test with verbose output
#   QUICK_ROLES=1 ./tools/test.sh            Test only 4 representative roles (faster)

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Delete outdated code coverage report
CODE_COVERAGE_DIR="${BASE_DIR:?}/htmlcov"
rm -rf "${CODE_COVERAGE_DIR}"

# By default, tests run inside a Docker container that mirrors the CircleCI
# environment (same Python, OS, font stack and PostgreSQL version) so that a
# local run matches CI by construction. Pass --local to run on the host instead.
LOCAL_MODE=0

# Runs the assembled pytest invocation inside the CI-matching Docker container.
function run_tests_in_docker {
    local compose_file="${BASE_DIR}/docker-compose.test.yml"
    if ! command -v docker > /dev/null || ! docker compose version > /dev/null 2>&1; then
        echo "Docker (with the Compose plugin) is required to run tests in the default Docker mode." | print_error
        echo "Install Docker, or re-run with --local to use your host environment instead." | print_info
        exit 1
    fi
    # The project's .env is a bash-source file (it `source`s the venv), not a
    # docker-compose env file, so prevent Compose from auto-loading it for
    # variable substitution (this compose file uses no interpolation anyway).
    local compose=(docker compose --env-file /dev/null -f "${compose_file}")
    echo "Building the CI-matching test image (first run only)..." | print_info
    "${compose[@]}" build
    echo "Running tests inside Docker (cimg/python:3.13.11 + cimg/postgres:17.10, matching CI)..." | print_info
    "${compose[@]}" run --rm tests "$@"
}

# Prepares the host environment for a --local test run (database, settings, …).
function prepare_local_environment {
    require_installed

    ensure_webpack_bundle_exists

    require_database

    # When require_database falls back to the dockerized postgres, it exposes the
    # container on INTEGREAT_CMS_DOCKER_LISTEN_PORT. docker_settings hardcodes that
    # port, but test_settings (below) inherits from base settings and reads the
    # port from the env, so propagate it explicitly.
    if [[ "${DJANGO_SETTINGS_MODULE}" == "integreat_cms.core.docker_settings" ]]; then
        export INTEGREAT_CMS_DB_PORT="${INTEGREAT_CMS_DOCKER_LISTEN_PORT}"
    fi

    # Test-specific settings (dummy API keys, disabled listeners, etc.) are
    # configured in integreat_cms/core/test_settings.py.
    # Override the DJANGO_SETTINGS_MODULE that require_database sets to the base
    # settings, so pytest uses the test settings even when invoked via this script.
    export DJANGO_SETTINGS_MODULE="integreat_cms.core.test_settings"
}

# Disable re-importing of external news posts on demand
export INTEGREAT_CMS_EXTERNALNEWS_DISABLE_AUTO_REIMPORT=1


TESTS=()
PYTEST_PASSTHROUGH=()

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
        # Run on the host instead of inside the CI-matching Docker container
        --local) LOCAL_MODE=1;shift;;
        # Forward any other long flags (e.g. --update-snapshots) directly to pytest
        --*) PYTEST_PASSTHROUGH+=("$1");shift;;
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
    # Disable testmon when running in parallel — testmon conflicts with xdist
    # and causes sporadic User.DoesNotExist errors during fixture setup.
    if [[ -z "${VERBOSITY}" ]]; then
        PYTEST_ARGS+=("-p" "no:testmon")
    else
        # Serial mode (verbose): safe to use testmon
        PYTEST_ARGS+=("--testmon-noselect")
    fi
fi

# Determine whether coverage data should be collected
if [[ -z "${CHANGED}" ]] && (( ${#TESTS[@]} == 0 )); then
    PYTEST_ARGS+=("--cov=integreat_cms" "--cov-report=html")
    # The fail_under threshold in pyproject.toml is only meaningful for the
    # full suite — a filtered run (-k/-m) always yields partial coverage, so
    # don't fail it on the threshold.
    if [[ -n "${KW_EXPR}" ]] || [[ -n "${MARKER}" ]]; then
        PYTEST_ARGS+=("--cov-fail-under=0")
    fi
fi

if [[ -n "${KW_EXPR}" ]] || [[ -n "${MARKER}" ]] || (( ${#TESTS[@]} )); then
    TEST_MESSAGE=""
    if [[ -n "${KW_EXPR}" ]]; then
        TEST_MESSAGE+=" \"${KW_EXPR}\""
        PYTEST_ARGS+=("-k" "${KW_EXPR}")
    fi
    if [[ -n "${MARKER}" ]]; then
        TEST_MESSAGE+=" with ${MARKER}"
        PYTEST_ARGS+=("-m" "${MARKER}")
    fi
    FILES=()
    # Check whether test paths exist
    for t in "${TESTS[@]}"; do
        if [[ -e "${t%%::*}" ]]; then
            # Adapt message and append to pytest arguments
            FILES+=("${t}")
            PYTEST_ARGS+=("${t}")
        elif [[ -n "${t}" ]]; then
            # If the test path does not exist but was non-zero, show an error
            echo -e "${t%%::*}: No such file or directory" | print_error
            exit 1
        fi
    done
    FILES_MESSAGE=$(join_by ", " "${FILES[@]}")
    TEST_MESSAGE+=" in $FILES_MESSAGE"
fi

PYTEST_ARGS+=("${PYTEST_PASSTHROUGH[@]}")

if [[ "${LOCAL_MODE}" -eq 0 ]]; then
    echo -e "Running all tests${TEST_MESSAGE}${CHANGED_MESSAGE} in Docker..." | print_info
    run_tests_in_docker "${PYTEST_ARGS[@]}"
else
    prepare_local_environment
    "$(dirname "${BASH_SOURCE[0]}")/prune_pdf_cache.sh"
    echo -e "Running all tests${TEST_MESSAGE}${CHANGED_MESSAGE}..." | print_info
    deescalate_privileges pytest "${PYTEST_ARGS[@]}"
fi
echo "✔ Tests successfully completed " | print_success

if [[ -d "${CODE_COVERAGE_DIR}" ]]; then
    echo -e "Open the following file in your browser to view the test coverage:\n" | print_info
    echo -e "\tfile://${CODE_COVERAGE_DIR}/index.html\n" | print_bold
fi
