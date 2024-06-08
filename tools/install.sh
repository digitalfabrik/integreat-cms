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

if [[ -n "${PYTHON}" ]]; then
    PYTHON=$(command -v "${PYTHON}")
    if [[ ! -x "${PYTHON}" ]]; then
        echo "The given python command '${PYTHON}' is not executable." | print_error
        exit 1
    fi
else
    # Default python binary
    PYTHON="python3"
fi

# Check if requirements are satisfied
# Define the required python version
required_python_version="3.11"
if [[ ! -x "$(command -v python3)" ]]; then
    echo "Python3 is not installed. Please install Python ${required_python_version} or higher manually and run this script again."  | print_error
    exit 1
fi
# Get the python version (the format is "Python 3.X.Z")
python_version=$(${PYTHON} --version | cut -d" " -f2)
if [[ $(major "$python_version") -lt $(major "$required_python_version") ]] || \
   [[ $(major "$python_version") -eq $(major "$required_python_version") ]] && [[ $(minor "$python_version") -lt $(minor "$required_python_version") ]]; then
    echo "python version ${required_python_version} is required, but version ${python_version} is installed. Please install a recent version manually and run this script again."  | print_error
    echo -e "If you installed higher python version manually which is not your default python3, please pass the alternative python interpreter (e.g. python3.11) to the script:\n" | print_info
    echo -e "\t$(dirname "${BASH_SOURCE[0]}")/install.sh --python python3.11\n" | print_bold
    exit 1
fi
# Check if pip is installed
if [[ ! -x "$(command -v pip3)" ]]; then
    echo "Pip for Python3 is not installed. Please install python3-pip manually and run this script again."  | print_error
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
required_node_version="18"
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

# Check if virtual environment exists
if [[ -d ".venv" ]] && [[ "$(.venv/bin/python3 --version)" != "$(${PYTHON} --version)" ]]; then
    echo "The given $(${PYTHON} --version) version differs from $(.venv/bin/python3 --version) of virtual environment." | print_warning
    echo "Deleting the outdated virtual environment..." | print_info
    rm -rf .venv
fi

# Check if virtual environment exists
if [[ ! -f ".venv/bin/activate" ]]; then
    echo "Creating virtual environment for $(${PYTHON} --version)..." | print_info
    # Check whether venv creation succeeded
    if ! ${PYTHON} -m venv .venv; then
        # Check whether it would succeed without pip
        if ${PYTHON} -m venv --without-pip .venv &> /dev/null; then
            # Remove "broken" venv without pip
            rm -rf .venv
            # Determine which package needs to be installed
            if [[ "$(${PYTHON} --version)" == "$(python3 --version)" ]]; then
                VENV_PACKAGE="python3-venv"
            else
                MINOR_PYTHON=$(minor "${python_version}")
                VENV_PACKAGE="python3.${MINOR_PYTHON}-venv"
            fi
            echo "Pip is not available inside the virtual environment. Please install ${VENV_PACKAGE} manually and run this script again."  | print_error
            exit 1
        fi
    fi
fi

# Activate virtual environment
source .venv/bin/activate

# Install pip dependencies
# shellcheck disable=SC2102
pip install -e .[dev-pinned,pinned]
echo "✔ Installed Python dependencies" | print_success

# Install pre-commit-hooks if --pre-commit option is given
if [[ -n "${PRE_COMMIT}" ]]; then
    echo "Installing pre-commit hooks..." | print_info
    # Install pre-commit hook for black code style
    pre-commit install
    echo "✔ Installed pre-commit hooks" | print_success
fi

echo -e "\n✔ The Integreat CMS was successfully installed 😻" | print_success
echo -e "Use the following command to start the development server:\n" | print_info
echo -e "\t$(dirname "${BASH_SOURCE[0]}")/run.sh\n" | print_bold
