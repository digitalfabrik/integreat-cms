#!/bin/bash

# This script installs the CMS in a local virtual environment without the need for docker or any other virtualization technology.
# A Postgres SQL server is needed to run the CMS (optionally inside a docker container).

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

ensure_not_root

echo "Checking system requirements..." | print_info

# Parse command line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    --clean) CLEAN=1; shift 1;;
    --pre-commit) PRE_COMMIT=1; shift 1;;
    --python) PYTHON="$2"; shift 2;;
    --python=*) PYTHON="${1#*=}"; shift 1;;
    *) echo "Unknown option: $1" | print_error; exit 1;;
  esac
done

# If no interpreter is given, uv selects one which satisfies "requires-python" of pyproject.toml
if [[ -n "${PYTHON}" ]]; then
    PYTHON=$(command -v "${PYTHON}")
    if [[ ! -x "${PYTHON}" ]]; then
        echo "The given python command '${PYTHON}' is not executable." | print_error
        exit 1
    fi
fi

# Check if requirements are satisfied
# Check if uv is installed (it provisions the Python interpreter required by pyproject.toml itself)
if [[ ! -x "$(command -v uv)" ]]; then
    echo "The package manager uv is not installed. Please install it manually and run this script again."  | print_error
    echo -e "See https://docs.astral.sh/uv/getting-started/installation/ for the available installation methods.\n" | print_info
    exit 1
fi
# Check if postgres instance is running on host system or database backend is installed
if ! { [[ -x "$(command -v docker)" ]] || [[ -x "$(command -v psql)" ]] || nc -z localhost 5432 > /dev/null 2>&1; }; then
    echo "In order to run the database, you need either Docker (recommended) or PostgreSQL. Please install at least one of them manually and run this script again."
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
# Define the required npm version
required_node_version="22"
# Check if nodejs is installed
if [[ ! -x "$(command -v node)" ]]; then
    echo "The package nodejs is not installed. Please install nodejs version ${required_node_version} or higher manually and run this script again."  | print_error
    exit 1
fi
# Get the node version (the format is vXX.YY.ZZ)
node_version=$(node -v | cut -c2-)
# Check if required node version is installed
if [[ $(major "$node_version") -lt "$required_node_version" ]] ; then
    echo "nodejs version ${required_node_version} or higher is required, but version ${node_version} is installed. Please install a supported version manually and run this script again."  | print_error
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
if [[ -n "${CLEAN}" ]]; then
    echo "Removing installed dependencies and compiled static files..." | print_info
    # Report deleted files but only the explicitly deleted directories
    rm -rfv .venv node_modules "${PACKAGE_DIR:?}/static/dist" | grep -E -- "'.venv'|'node_modules'|'${PACKAGE_DIR}/static/dist'" || true
fi

# Install npm dependencies
echo "Installing JavaScript dependencies..." | print_info
npm ci --no-fund
echo "✔ Installed JavaScript dependencies" | print_success

# Install the exact versions from the lock file into .venv (created by uv if it does not exist yet)
echo "Installing Python dependencies..." | print_info
if [[ -n "${PYTHON}" ]]; then
    uv sync --locked --python "${PYTHON}"
else
    uv sync --locked
fi

# Activate virtual environment
source .venv/bin/activate

echo "✔ Installed Python dependencies" | print_success

# Install pre-commit-hooks if --pre-commit option is given
if [[ -n "${PRE_COMMIT}" ]]; then
    echo "Installing pre-commit hooks..." | print_info
    # Install pre-commit hooks
    pre-commit install
    echo "✔ Installed pre-commit hooks" | print_success
fi

echo -e "\n✔ The Integreat CMS was successfully installed 😻" | print_success
echo -e "Use the following command to start the development server:\n" | print_info
echo -e "\t$(dirname "${BASH_SOURCE[0]}")/run.sh\n" | print_bold
