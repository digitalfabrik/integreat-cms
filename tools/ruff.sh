#!/bin/bash

# This script can be used to format the python code with ruff.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

PATHS=()

# Parse given command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        *) PATHS+=("$1");shift;;
    esac
done

if [ ${#PATHS[@]} -gt 0 ]; then
    # Check whether paths exist
    for p in "${PATHS[@]}"; do
        if [[ -e "${p%%::*}" ]]; then
            RUFF_ARGS+=("${p}")
        elif [[ -n "${p}" ]]; then
            # If the path does not exist but was non-zero, show an error
            echo -e "${p%%::*}: No such file or directory" | print_error
            exit 1
        fi
    done
else
    PATHS=("$BASE_DIR")
fi

# shellcheck source=./tools/ruff_check.sh
"$(dirname "${BASH_SOURCE[0]}")/ruff_check.sh" "${PATHS[@]}"

# shellcheck source=./tools/ruff_format.sh
"$(dirname "${BASH_SOURCE[0]}")/ruff_format.sh" "${PATHS[@]}"
