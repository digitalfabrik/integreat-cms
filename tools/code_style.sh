#!/bin/bash

# This script can be used to runs all of our code style tools: ruff, mypy, djlint, eslint and prettier

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Run ruff
bash "${DEV_TOOL_DIR}/ruff.sh" || :

# Run mypy
bash "${DEV_TOOL_DIR}/mypy.sh" || :

# Run djlint
bash "${DEV_TOOL_DIR}/djlint.sh" || :

# Run eslint
bash "${DEV_TOOL_DIR}/eslint.sh" || :

# Run prettier
bash "${DEV_TOOL_DIR}/prettier.sh" || :
