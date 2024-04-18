#!/bin/bash

# This script can be used to format the static files with prettier

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Run prettier
echo "Starting frontend tests with vitest..." | print_info
npm run test
echo "✔ Frontend tests finished" | print_success
