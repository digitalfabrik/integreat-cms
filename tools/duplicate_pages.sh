#!/bin/bash

# This script duplicates all pages of the first region in the database

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
require_database

# Initialize the Redis cache to make sure the cache is invalidated
configure_redis_cache

deescalate_privileges integreat-cms-cli shell --verbosity "${SCRIPT_VERBOSITY}" < "${DEV_TOOL_DIR}/_duplicate_pages.py"
echo "✔ Duplicated pages" | print_success
