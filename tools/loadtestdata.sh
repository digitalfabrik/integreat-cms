#!/bin/bash

# This script imports test data into the database.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
require_database

cp "${PACKAGE_DIR}/static/src/logos/integreat/integreat-logo.png" "${PACKAGE_DIR}/media/global/integreat-logo.png"
cp "${PACKAGE_DIR}/static/src/logos/malte/malte-logo.png" "${PACKAGE_DIR}/media/global/malte-logo.png"
deescalate_privileges integreat-cms-cli loaddata "${PACKAGE_DIR}/cms/fixtures/test_data.json" --verbosity "${SCRIPT_VERBOSITY}"

echo "✔ Imported test data" | print_success
