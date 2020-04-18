#!/bin/bash

# This script checks if all dependencies in the lock files are up to date and increments the version numbers if necessary.

# Check if script is running as root
if [ $(id -u) = 0 ]; then
    # Check if script was invoked by the root user or with sudo
    if [ -z "$SUDO_USER" ]; then
        echo "Please do not execute update.sh as your root user because it would set the wrong file permissions of your virtual environment." >&2
        exit 1
    else
        # Call this script again as the user who executed sudo
        sudo -u $SUDO_USER env PATH="$PATH" $0
        # Exit with code of subprocess
        exit $?
    fi
fi

cd $(dirname "$BASH_SOURCE")/..

# Check if npm dependencies are up to date
npx npm-check --update-all --skip-unused

# Check if pip dependencies are up to date
pipenv update
