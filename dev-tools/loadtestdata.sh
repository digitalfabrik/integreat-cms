#!/bin/bash

# This script imports test data into the database.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
require_database

deescalate_privileges pipenv run integreat-cms-cli loaddata "${PACKAGE_DIR}/cms/fixtures/test_data.json"
echo "✔ Imported test data" | print_success
