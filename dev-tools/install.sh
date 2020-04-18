#!/bin/bash

# This script installs the CMS in a local virtual environment without the need for docker or any other virtualization technology.
# A Postgres SQL server is needed to run the CMS (optionally inside a docker container).

# Check if requirements are satisfied
if [ ! -x "$(command -v python3)" ]; then
    echo "Python3 is not installed. Please install it manually and run this script again." >&2
    exit 1
fi
if [ ! -x "$(command -v pip3)" ]; then
    echo "Pip for Python3 is not installed. Please install python3-pip manually and run this script again." >&2
    exit 1
fi
if [ ! -x "$(command -v pipenv)" ]; then
    echo "Pipenv for Python3 is not installed. Please install python3-pipenv manually and run this script again." >&2
    exit 1
fi
if [ ! -x "$(command -v npm)" ]; then
    echo "The package npm is not installed. Please install npm version 5 or higher manually and run this script again." >&2
    exit 1
fi
npm_version=$(npm -v)
if [ "${npm_version%%.*}" -lt 5 ]; then
    echo "npm version 5 or higher is required, but version $npm_version is installed. Please install a recent version manually and run this script again." >&2
    exit 1
fi

# Check if script is running as root
if [ $(id -u) = 0 ]; then
    # Check if script was invoked by the root user or with sudo
    if [ -z "$SUDO_USER" ]; then
        echo "Please do not execute install.sh as your root user because it would set the wrong file permissions of your virtual environment." >&2
        exit 1
    else
        # Call this script again as the user who executed sudo
        sudo -u $SUDO_USER env PATH="$PATH" $0
        # Exit with code of subprocess
        exit $?
    fi
fi

cd $(dirname "$BASH_SOURCE")/..
npm install
PIPENV_VENV_IN_PROJECT=1 pipenv install
