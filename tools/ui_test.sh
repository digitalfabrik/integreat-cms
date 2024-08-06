#!/bin/bash

# This script executes the tests and starts the database docker container if necessary.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Delete outdated code coverage report
CODE_COVERAGE_DIR="${BASE_DIR:?}/htmlcov"
rm -rf "${CODE_COVERAGE_DIR}"

require_installed

ensure_webpack_bundle_exists

require_database

# Set dummy key to enable SUMM.AI during testing
export INTEGREAT_CMS_SUMM_AI_API_KEY="dummy"

# Set dummy key to enable DeepL during testing
export INTEGREAT_CMS_DEEPL_AUTH_KEY="dummy"

# Set dummy key to enable Textlab during testing
export INTEGREAT_CMS_TEXTLAB_API_KEY="dummy"
# Set Google credentials and project ID to enable Google Translate during testing
export INTEGREAT_CMS_GOOGLE_CREDENTIALS="dummy.json"
export INTEGREAT_CMS_GOOGLE_PROJECT_ID="dummy"

# Disable linkcheck listeners during testing
export INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS=1

# Disable background tasks during testing
export INTEGREAT_CMS_BACKGROUND_TASKS_ENABLED=0

# Necessary in order to run playwright tests
export DJANGO_ALLOW_ASYNC_UNSAFE="True"

# Parse given command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        # Verbosity for pytest
        -v|-vv|-vvv|-vvvv) VERBOSITY="$1";shift;;
    esac
done

# The default pytests args we use
PYTEST_ARGS=("--disable-warnings" "--color=yes")

if [[ -n "${VERBOSITY}" ]]; then
    PYTEST_ARGS+=("$VERBOSITY")
else
    PYTEST_ARGS+=("--quiet" "--numprocesses=auto")
fi

PYTEST_ARGS+=("--testmon-noselect")

"$(dirname "${BASH_SOURCE[0]}")/prune_pdf_cache.sh"

echo -e "Running all user interface tests..." | print_info
deescalate_privileges pytest "${PYTEST_ARGS[@]}" ui_tests
echo "✔ Tests successfully completed " | print_success
