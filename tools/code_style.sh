#!/bin/bash

# This script can be used to runs all of our code style tools: isort, djlint, black, pylint, eslint and prettier

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Run isort
bash "${DEV_TOOL_DIR}/isort.sh"

# Run black
bash "${DEV_TOOL_DIR}/black.sh"

# Run djlint
bash "${DEV_TOOL_DIR}/djlint.sh"

# Run pylint
bash "${DEV_TOOL_DIR}/pylint.sh"

# Run eslint
bash "${DEV_TOOL_DIR}/eslint.sh"

# Run prettier
bash "${DEV_TOOL_DIR}/prettier.sh"
