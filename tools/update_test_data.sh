#!/bin/bash

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
require_database

deescalate_privileges integreat-cms-cli dumpdata --natural-primary --natural-foreign --exclude auth --exclude contenttypes --o integreat_cms/cms/fixtures/test_data.json
