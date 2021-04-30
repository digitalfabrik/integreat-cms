#!/bin/bash

# This script can be used to generate migrations and applying them afterwards.
# It can be used with the postgres docker container as well as a standalone installation.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_database
migrate_database
