#!/bin/bash

# This script imports test data into the database.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
require_database

export INTEGREAT_CMS_LINKCHECK_DISABLE_LISTENERS=1

deescalate_privileges integreat-cms-cli loaddata "${PACKAGE_DIR}/cms/fixtures/test_data.json" --verbosity "${SCRIPT_VERBOSITY}"
echo "✔ Imported test data" | print_success
