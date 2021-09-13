#!/bin/bash

# This script installs the CMS in a local virtual environment without the need for docker or any other virtualization technology.
# A Postgres SQL server is needed to run the CMS (optionally inside a docker container).

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

ensure_not_root

echo "Checking system requirements..." | print_info
# Check if requirements are satisfied
if [[ ! -x "$(command -v python3.7)" ]]; then  echo "Python3.7 is not installed. Please install it manually and run this script again."  | print_error
    exit 1
fi
if [[ ! -x "$(command -v pip3)" ]]; then
    echo "Pip for Python3 is not installed. Please install python3-pip manually and run this script again."  | print_error
    exit 1
fi
# Define the required pipenv version
required_pipenv_version="2018.10.9"
# Check if pipenv is installed
if [[ ! -x "$(command -v pipenv)" ]]; then
    # Check if pipenv is installed in the pip user directory
    if [[ -x ~/.local/bin/pipenv ]]; then
        PATH="${PATH}:${HOME}/.local/bin"
    else
        echo "Pipenv for Python3 is not installed. Please install version ${required_pipenv_version} or later manually (e.g. with 'pip3 install pipenv --user') and run this script again."  | print_error
        exit 1
    fi
fi
# Get the pipenv version (the format is "pipenv, version XX.YY.ZZ" or "pipenv, version YYYY.MM.DD")
pipenv_version=$(pipenv --version | cut -d" " -f3)
# Check pipenv version requirements (if major versions are identical, check for the minor version)
if [[ $(major "$pipenv_version") -lt $(major "$required_pipenv_version") ]] || \
   [[ $(major "$pipenv_version") -eq $(major "$required_pipenv_version") ]] && [[ $(minor "$pipenv_version") -lt $(minor "$required_pipenv_version") ]]; then
    echo "pipenv version ${required_pipenv_version} is required, but version ${pipenv_version} is installed. Please install a recent version manually (e.g. with 'pip3 install pipenv --user') and run this script again."  | print_error
    exit 1
fi
# Check if database backend is installed
if [[ ! -x "$(command -v docker)" ]] && [[ ! -x "$(command -v psql)" ]]; then
    echo "In order to run the database, you need either Docker (recommended) or PostgreSQL. Please install at least one of them manually and run this script again." | print_error
    exit 1
fi
# Define the required npm version
required_npm_version="7"
# Check if npm is installed
if [[ ! -x "$(command -v npm)" ]]; then
    echo "The package npm is not installed. Please install npm version ${required_npm_version} or higher manually and run this script again."  | print_error
    exit 1
fi
npm_version=$(npm -v)
# Check if required npm version is installed
if [[ $(major "$npm_version") -lt "$required_npm_version" ]]; then
    echo "npm version ${required_npm_version} or higher is required, but version ${npm_version} is installed. Please install a recent version manually (e.g. with 'npm install -g npm') and run this script again."  | print_error
    exit 1
fi
# Check if nodejs is installed
if [[ ! -x "$(command -v node)" ]]; then
    echo "The package nodejs is not installed. Please install nodejs version 12, 14 or 15 manually and run this script again."  | print_error
    exit 1
fi
# Get the node version (the format is vXX.YY.ZZ)
node_version=$(node -v | cut -c2-)
# Check node version requirements (12, 14 or 15)
if ! [[ $(major "$node_version") =~ ^(12|14|15)$ ]] ; then
    echo "nodejs version 12, 14 or 15 is required, but version ${node_version} is installed. Please install a supported version manually and run this script again."  | print_error
    exit 1
fi
# Check if nc (netcat) is installed
if [[ ! -x "$(command -v nc)" ]]; then
    echo "Netcat is not installed. Please install it manually and run this script again."  | print_error
    exit 1
fi
# Check if GNU gettext tools are installed
if [[ ! -x "$(command -v msguniq)" ]]; then
    echo "GNU gettext tools are not installed. Please install gettext manually and run this script again."  | print_error
    exit 1
fi
# Check if pcregrep is installed
if [[ ! -x "$(command -v pcregrep)" ]]; then
    echo "PCRE grep is not installed. Please install pcregrep manually and run this script again."  | print_error
    exit 1
fi
echo "✔ All system requirements are satisfied" | print_success

# Check if the --clean option is given
if [[ "$*" == *"--clean"* ]]; then
    echo "Removing installed dependencies and compiled static files..." | print_info
    # Report deleted files but only the explicitly deleted directories
    rm -rfv .venv node_modules "${PACKAGE_DIR:?}/static/dist" | grep -E -- "'.venv'|'node_modules'|'${PACKAGE_DIR}/static/dist'"
fi

# Install npm dependencies
echo "Installing JavaScript dependencies..." | print_info
npm install --no-fund
echo "✔ Installed JavaScript dependencies" | print_success

# Check if working directory contains space (if so, pipenv in project won't work)
if ! pwd | grep -q " "; then
    export PIPENV_VENV_IN_PROJECT=1
else
    echo "Warning: The path to your project directory contains spaces, therefore the virtual environment will be created inside '~/.local/share/virtualenvs/'." | print_warning
fi

# Install pip dependencies
pipenv install --dev
echo "✔ Installed Python dependencies" | print_success

# Install pre-commit-hooks if --pre-commit option is given
if [[ "$*" == *"--pre-commit"* ]]; then
    echo "Installing pre-commit hooks..." | print_info
    # Install pre-commit hook for black code style
    pipenv run pre-commit install
    echo "✔ Installed pre-commit hooks" | print_success
fi

echo -e "\n✔ The Integreat CMS was successfully installed 😻" | print_success
echo -e "Use the following command to start the development server:\n" | print_info
echo -e "\t$(dirname "${BASH_SOURCE[0]}")/run.sh\n" | print_bold
