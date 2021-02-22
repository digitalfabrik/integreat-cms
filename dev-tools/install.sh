#!/bin/bash

# This script installs the CMS in a local virtual environment without the need for docker or any other virtualization technology.
# A Postgres SQL server is needed to run the CMS (optionally inside a docker container).

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

# Check if requirements are satisfied
if [ ! -x "$(command -v python3.7)" ]; then
    echo "Python3.7 is not installed. Please install it manually and run this script again." >&2
    exit 1
fi
if python3.7 -m platform | grep -qi Ubuntu && ! dpkg -l | grep -qi python3.7-dev; then
    echo "You are on Ubuntu and Python3.7-dev is not installed. Please install python3.7-dev manually and run this script again." >&2
    exit 1
fi
if [ ! -x "$(command -v pip3)" ]; then
    echo "Pip for Python3 is not installed. Please install python3-pip manually and run this script again." >&2
    exit 1
fi
if [ ! -x "$(command -v pipenv)" ]; then
    echo "Pipenv for Python3 is not installed. Please install it manually and run this script again." >&2
    echo "The recommended way of installing pipenv is 'pip3 install pipenv --user'." >&2
    echo "If you use this method, you might have to add 'export PATH=\$PATH:~/.local/bin' to your default shell config (e.g. '~/.bashrc' or '~/.zshrc')." >&2
    exit 1
fi
if [ ! -x "$(command -v npm)" ]; then
    echo "The package npm is not installed. Please install npm version 5 or higher manually and run this script again." >&2
    exit 1
fi
npm_version=$(npm -v)
if [ "${npm_version%%.*}" -lt 7 ]; then
    echo "npm version 7 or higher is required, but version $npm_version is installed. Please install a recent version manually (e.g. with 'npm install -g npm') and run this script again." >&2
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

# Install npm dependencies
npm install

# Check if working directory contains space (if so, pipenv in project won't work)
if ! pwd | grep -q " "; then
    export PIPENV_VENV_IN_PROJECT=1
else
    echo "Warning: The path to your project directory contains spaces, therefore the virtual environment will be created inside '~/.local/share/virtualenvs/'."
fi

# Install pip dependencies
pipenv install --dev

# Install pre-commit hook for black code style
pipenv run pre-commit install
