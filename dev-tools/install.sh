#!/bin/bash

# This script installs the CMS in a local virtual environment without the need for docker or any other virtualization technology.
# A Postgres SQL server is needed to run the CMS (optionally inside a docker container).

# This function prints the major version of a string in the format XX.YY.ZZ
function major {
    # Split by "." and take the first element for the major version
    echo "$1" | cut -d. -f1
}

# This function prints the minor version of a string in the format XX.YY.ZZ
function minor {
    # Split by "." and take the second element for the minor version
    echo "$1" | cut -d. -f2
}

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
    echo "You are on Ubuntu and python3.7-dev is not installed. Please install python3.7-dev manually and run this script again." >&2
    exit 1
fi
if [ ! -x "$(command -v pip3)" ]; then
    echo "Pip for Python3 is not installed. Please install python3-pip manually and run this script again." >&2
    exit 1
fi
# Define the required pipenv version
required_pipenv_version="2018.10.9"
# Check if pipenv is installed
if [ ! -x "$(command -v pipenv)" ]; then
    # Check if pipenv is installed in the pip user directory
    if [[ -x ~/.local/bin/pipenv ]]; then
        echo "You have installed pipenv with pip, but the pip user directory is not contained in the \$PATH variable. Please add 'export PATH=\$PATH:~/.local/bin' to your default shell config (e.g. '~/.bashrc' or '~/.zshrc')." >&2
    else
        echo "Pipenv for Python3 is not installed. Please install version ${required_pipenv_version} or later manually (e.g. with 'pip3 install pipenv --user') and run this script again." >&2
    fi
    exit 1
fi
# Get the pipenv version (the format is "pipenv, version XX.YY.ZZ" or "pipenv, version YYYY.MM.DD")
pipenv_version=$(pipenv --version | cut -d" " -f3)
# Check pipenv version requirements (if major versions are identical, check for the minor version)
if [[ $(major "$pipenv_version") -lt $(major "$required_pipenv_version") ]] || \
   [[ $(major "$pipenv_version") -eq $(major "$required_pipenv_version") ]] && [[ $(minor "$pipenv_version") -lt $(minor "$required_pipenv_version") ]]; then
    echo "pipenv version ${required_pipenv_version} is required, but version ${pipenv_version} is installed. Please install a recent version manually (e.g. with 'pip3 install pipenv --user') and run this script again." >&2
    exit 1
fi
# Define the required npm version
required_npm_version="7"
# Check if npm is installed
if [ ! -x "$(command -v npm)" ]; then
    echo "The package npm is not installed. Please install npm version ${required_npm_version} or higher manually and run this script again." >&2
    exit 1
fi
npm_version=$(npm -v)
# Check if required npm version is installed
if [[ $(major "$npm_version") -lt "$required_npm_version" ]]; then
    echo "npm version ${required_npm_version} or higher is required, but version ${npm_version} is installed. Please install a recent version manually (e.g. with 'npm install -g npm') and run this script again." >&2
    exit 1
fi
# Check if nodejs is installed
if [ ! -x "$(command -v node)" ]; then
    echo "The package nodejs is not installed. Please install nodejs version 12, 14 or 15 manually and run this script again." >&2
    exit 1
fi
# Get the node version (the format is vXX.YY.ZZ)
node_version=$(node -v | cut -c2-)
# Check node version requirements (12, 14 or 15)
if ! [[ $(major "$node_version") =~ ^(12|14|15)$ ]] ; then
    echo "nodejs version 12, 14 or 15 is required, but version ${node_version} is installed. Please install a supported version manually and run this script again." >&2
    exit 1
fi
# Check if nc (netcat) is installed
if [ ! -x "$(command -v nc)" ]; then
    echo "Netcat is not installed. Please install it manually and run this script again." >&2
    exit 1
fi
# Check if GNU gettext tools are installed
if [ ! -x "$(command -v msguniq)" ]; then
    echo "GNU gettext tools are not installed. Please install gettext manually and run this script again." >&2
    exit 1
fi
# Check if pcregrep is installed
if [ ! -x "$(command -v pcregrep)" ]; then
    echo "PCRE grep is not installed. Please install pcregrep manually and run this script again." >&2
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

if [ "$1" == "--clean" ]; then
  echo "Removing installed dependencies and compiled static files."
  rm -rf .venv node_modules src/cms/static
fi

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
