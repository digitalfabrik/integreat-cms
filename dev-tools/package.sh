#!/bin/bash

# This script builds the CMS into a standalone and reusable python package.
# It requires that the cms and its dependencies are already installed locally.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Compile CSS file
pipenv run npm run prod

# Compile translation file
pipenv run integreat-cms-cli compilemessages

# Create debian package
python3 setup.py --command-packages=stdeb.command bdist_deb
