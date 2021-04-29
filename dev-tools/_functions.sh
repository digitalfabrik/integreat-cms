#!/bin/bash

# This file contains utility functions which can be used in the dev-tools.

# Do not continue execution if one of the commands fail
set -eo pipefail -o functrace

# Check if the --verbose option is given
if [[ "$*" == *"--verbose"* ]]; then
    # The shell writes a trace for each command to standard error after it expands the command and before it executes it.
    set -vx
fi

# The name of the used database docker container
DOCKER_CONTAINER_NAME="integreat_django_postgres"
# Change to dev tools directory
cd "$(dirname "${BASH_SOURCE[0]}")"
# The absolute path to the dev tools directory
DEV_TOOL_DIR=$(pwd)
# Change to base directory
cd ..
# The absolute path to the base directory of the repository
BASE_DIR=$(pwd)
# The filename of the currently running script
SCRIPT_NAME=$(basename "$0")
# The absolute path to the currently running script (required to allow restarting with different permissions
SCRIPT_PATH="${DEV_TOOL_DIR}/${SCRIPT_NAME}"
# The arguments which were passed to the currently running script
SCRIPT_ARGS=("$@")

# Set the pipenv verbosity based on whether pipenv is running inside a virtual environment or not.
if [[ -n "$VIRTUAL_ENV" ]]; then
    export PIPENV_VERBOSITY=-1
fi

# This function prints the given input lines in red color
function print_error {
    while IFS= read -r line; do
        echo -e "\e[1;31m$line\e[0;39m" >&2
    done
}

# This function prints the given input lines in green color
function print_success {
    while IFS= read -r line; do
        echo -e "\e[1;32m$line\e[0;39m"
    done
}

# This function prints the given input lines in orange color
function print_warning {
    while IFS= read -r line; do
        echo -e "\e[1;33m$line\e[0;39m"
    done
}

# This function prints the given input lines in blue color
function print_info {
    while IFS= read -r line; do
        echo -e "\e[1;34m$line\e[0;39m"
    done
}

# This function prints the given input lines in bold white
function print_bold {
    while IFS= read -r line; do
        echo -e "\e[1m$line\e[0m"
    done
}

# This function prints the given prefix in the given color in front of the stdin lines. If no color is given, white (37) is used.
# This is useful for commands which run in the background to separate its output from other commands.
function print_prefix {
    while IFS= read -r line; do
        echo -e "\e[1;${2:-37};40m[$1]\e[0m $line"
    done
}

# This function prints the given input lines with a nice little border to separate it from the rest of the content.
# Pipe your content to this function.
function print_with_borders {
    echo "┌──────────────────────────────────────"
    while IFS= read -r line; do
        echo "│ $line"
    done
    echo -e "└──────────────────────────────────────\n"
}

# Check if the --help option is given
if [[ "$*" == *"--help"* ]] || [[ "$*" == *"-h"* ]]; then
    echo -e "For usage details, see documentation:\n" | print_info
    echo -e "\thttps://integreat.github.io/integreat-cms/dev-tools.html\n" | print_bold
    exit
fi

# This function executes the given command with the user who invoked sudo
function deescalate_privileges {
    # Check if command is running as root
    if [[ $(id -u) == 0 ]]; then
        # Check if script was invoked by the root user or with sudo
        if [[ -z "$SUDO_USER" ]]; then
            echo "Please do not execute ${SCRIPT_NAME} as root user." | print_error
            exit 1
        else
            # Call this command again as the user who executed sudo
            sudo -u "$SUDO_USER" PATH="$PATH" DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" "$@"
        fi
    else
        # If user already has low privileges, just call the given command(s)
        "$@"
    fi
}

# This function makes sure the current script is not executed as root
function ensure_not_root {
    # Check if script is running as root
    if [[ $(id -u) == 0 ]]; then
        # Check if script was invoked by the root user or with sudo
        if [[ -z "$SUDO_USER" ]]; then
            echo "Please do not execute ${SCRIPT_NAME} as root user." | print_error
            exit 1
        else
            echo "No need to execute ${SCRIPT_NAME} with sudo. It is automatically restarted with lower privileges." | print_info
            # Call this script again as the user who executed sudo
            deescalate_privileges "${SCRIPT_PATH}" "${SCRIPT_ARGS[@]}"
            # Exit with code of subprocess
            exit $?
        fi
    fi
}

# This function makes sure the current script is executed with sudo
function ensure_root {
    # Check if script is not running as root
    if ! [[ $(id -u) == 0 ]]; then
        echo "The script ${SCRIPT_NAME} needs root privileges to connect to the docker deamon. It is be automatically restarted with sudo." | print_warning
        # Call this script again as root (pass -E because we want the user's environment, not root's)
        sudo -E PATH="$PATH" "${SCRIPT_PATH}" "${SCRIPT_ARGS[@]}"
        # Exit with code of subprocess
        exit $?
    elif [[ -z "$SUDO_USER" ]]; then
        echo "Please do not run ${SCRIPT_NAME} as root user, use sudo instead." | print_error
        exit 1
    fi
}

# This function migrates the database
function migrate_database {
    # Check for the variable DATABASE_MIGRATED to prevent multiple subsequent migration commands
    if [[ -z "$DATABASE_MIGRATED" ]]; then
        echo "Migrating database..." | print_info
        # Make migrations for all inbuilt apps (in case they are not included in the packages)
        deescalate_privileges pipenv run integreat-cms-cli makemigrations
        # Make migrations for cms app
        deescalate_privileges pipenv run integreat-cms-cli makemigrations cms
        # Executing migrations
        deescalate_privileges pipenv run integreat-cms-cli migrate
        # Load the role fixtures
        deescalate_privileges pipenv run integreat-cms-cli loaddata src/cms/fixtures/roles.json
        echo "✔ Finished database migrations" | print_success
        DATABASE_MIGRATED=1
    fi
}

# This function creates a new postgres database docker container
function create_docker_container {
    echo "Create new database container..." | print_info
    # Run new container
    docker run -d --name "${DOCKER_CONTAINER_NAME}" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "${BASE_DIR}/.postgres:/var/lib/postgresql" -p 5433:5432 postgres > /dev/null
    echo -n "Waiting for postgres database container to be ready..."
    until docker exec -it "${DOCKER_CONTAINER_NAME}" psql -U integreat -d integreat -c "select 1" > /dev/null 2>&1; do
      sleep 0.1
      echo -n "."
    done
    echo -e "\n✔ Created database container" | print_success
    # Set up exit trap to stop docker container when script ends
    cleanup_docker_container
}

# This function starts an existing postgres database docker container
function start_docker_container {
    # Start the existing container
    docker start "${DOCKER_CONTAINER_NAME}" > /dev/null
    # Wait until container is ready and accepts database connections
    until docker exec -it "${DOCKER_CONTAINER_NAME}" psql -U integreat -d integreat -c "select 1" > /dev/null 2>&1; do
      sleep 0.1
    done
    echo "✔ Started database container" | print_success
    # Set up exit trap to stop docker container when script ends
    cleanup_docker_container
}

# This function stops an existing postgres database docker container
function stop_docker_container {
    # Stop the postgres database docker container if it was not running before
    docker stop "${DOCKER_CONTAINER_NAME}" > /dev/null
    echo -e "\nStopped database container" | print_info
}

# This function initializes a trap to stop the docker container when the script ends
function cleanup_docker_container {
    # The trap command overrides existing traps, so we have to check whether this function as invoked from the run.sh script
    if [[ -n "$KILL_TRAP" ]]; then
        trap "stop_docker_container; kill 0" EXIT
    else
        trap stop_docker_container EXIT
    fi
}

# This function makes sure a postgres database docker container is running
function ensure_docker_container_running {
    # Check if postgres database container is already running
    if [[ $(docker ps -q -f name="${DOCKER_CONTAINER_NAME}") ]]; then
        echo "Database container is already running" | print_info
    else
        # Check if stopped container is available
        if [[ $(docker ps -aq -f status=exited -f name="${DOCKER_CONTAINER_NAME}") ]]; then
            # Start the existing container
            start_docker_container
        else
            # Run new container
            create_docker_container
            # Migrate database
            migrate_database
            # Import test data
            bash "${DEV_TOOL_DIR}/loadtestdata.sh"
        fi
    fi
}

# This function makes sure a database is available
function require_database {
    # Check if local postgres server is running
    if nc -w1 localhost 5432; then
        ensure_not_root
        echo "✔ Running PostgreSQL database detected" | print_success
        # Migrate database
        migrate_database
    else
        ensure_root
        # Check if docker socket is not available
        if ! docker ps > /dev/null; then
            echo "Please start either a local PostgreSQL database server or start the docker daemon so a database docker container can be created." | print_error
            exit 1
        fi

        # Set docker settings
        export DJANGO_SETTINGS_MODULE="backend.docker_settings"
        # Make sure a docker container is up and running
        ensure_docker_container_running
    fi
}

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
