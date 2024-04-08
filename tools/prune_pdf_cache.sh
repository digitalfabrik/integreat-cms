#!/bin/bash

# This script can be used to prune the pdf file cache.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

rm -rfv "${PACKAGE_DIR:?}/pdf"
echo "Removed PDF cache" | print_info
