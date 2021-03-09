#!/bin/bash

# This script builds the CMS into a standalone and reusable python package.
# It requires that the cms and its dependencies are already installed locally.

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

# Check if script is running as root
if [ $(id -u) = 0 ]; then
    # Check if script was invoked by the root user or with sudo
    if [ -z "$SUDO_USER" ]; then
        echo "Please do not execute package.sh as your root user because it would set the wrong file permissions for your static files." >&2
        exit 1
    else
        # Call this script again as the user who executed sudo
        sudo -u $SUDO_USER env PATH="$PATH" $0
        # Exit with code of subprocess
        exit $?
    fi
fi

cd $(dirname "$BASH_SOURCE")/..

# Compile CSS file
pipenv run npm run prod

# Compile translation file
pipenv run integreat-cms-cli compilemessages

# Create debian package
python3 setup.py --command-packages=stdeb.command bdist_deb
