#!/bin/bash

# This file contains utility functions which can be used in the tools.

# Do not continue execution if one of the commands fail
set -eo pipefail -o functrace

# Check if the --verbose option is given
if [[ "$*" == *"--verbose"* ]]; then
    # The shell writes a trace for each command to standard error after it expands the command and before it executes it.
    set -vx
fi

# The Port on which the Integreat CMS development server should be started (do not use 9000 since this is used for webpack)
INTEGREAT_CMS_PORT=8000
# The name of the used database docker container
DOCKER_CONTAINER_NAME="integreat_django_postgres"
# Write the path to the redis socket into this file if you want to use the unix socket connection for your dev redis cache
REDIS_SOCKET_LOCATION="./.redis_socket_location"
# Change to dev tools directory
cd "$(dirname "${BASH_SOURCE[0]}")"
# The absolute path to the dev tools directory
DEV_TOOL_DIR=$(pwd)
# Change to base directory
cd ..
# The absolute path to the base directory of the repository
BASE_DIR=$(pwd)
# The path to the package
PACKAGE_DIR_REL="integreat_cms"
PACKAGE_DIR="${BASE_DIR}/${PACKAGE_DIR_REL}"
# The filename of the currently running script
SCRIPT_NAME=$(basename "$0")
# The absolute path to the currently running script (required to allow restarting with different permissions
SCRIPT_PATH="${DEV_TOOL_DIR}/${SCRIPT_NAME}"
# The arguments which were passed to the currently running script
SCRIPT_ARGS=("$@")
# The verbosity of the output (can be one of {0,1,2,3})
SCRIPT_VERBOSITY="1"

# This function prints the given input lines in red color
function print_error {
    while IFS= read -r line; do
        echo -e "\x1b[1;31m$line\x1b[0;39m" >&2
    done
}

# This function prints the given input lines in green color
function print_success {
    while IFS= read -r line; do
        echo -e "\x1b[1;32m$line\x1b[0;39m"
    done
}

# This function prints the given input lines in orange color
function print_warning {
    while IFS= read -r line; do
        echo -e "\x1b[1;33m$line\x1b[0;39m"
    done
}

# This function prints the given input lines in blue color
function print_info {
    while IFS= read -r line; do
        echo -e "\x1b[1;34m$line\x1b[0;39m"
    done
}

# This function prints the given input lines in bold white
function print_bold {
    while IFS= read -r line; do
        echo -e "\x1b[1m$line\x1b[0m"
    done
}

# This function underlines the first paramter with the second
function print_underline {
    echo -e "$1\n$(echo "$1" | tr '[:print:]' "$2")"
}

# This function underlines the first paramter with "="
function print_heading {
    echo -e "$(print_underline "$1" =)\n"
}

# This function underlines the first paramter with "-"
function print_subheading {
    echo -e "$(print_underline "$1" -)\n"
}

# This function prints the given prefix in the given color in front of the stdin lines. If no color is given, white (37) is used.
# This is useful for commands which run in the background to separate its output from other commands.
function print_prefix {
    while IFS= read -r line; do
        echo -e "\x1b[1;${2:-37};40m[$1]\x1b[0m $line"
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

# This function colorizes a number based on its value
function colorize_number {
    if [[ "$1" -eq "0" ]]; then
        echo -e "\x1b[1m$1\x1b[0m"
    elif [[ "$1" -ge "0" ]]; then
        if [[ -n "$2" ]]; then
            NUM="+$1"
        else
            NUM="$1"
        fi
        echo -e "\x1b[1;32m$NUM\x1b[0;39m"
    else
        echo -e "\x1b[1;31m$1\x1b[0;39m"
    fi
}

# Check if the --help option is given
if [[ -z ${SKIP_HELP_COMMAND} ]]; then
    if [[ "$*" == *" --help "* ]] || [[ "$*" == *" -h "* ]]; then
        echo -e "For usage details, see documentation:\n" | print_info
        echo -e "\thttps://digitalfabrik.github.io/integreat-cms/tools.html\n" | print_bold
        exit
    fi
fi

# This function checks if the integreat cms is installed
function require_installed {
    if [[ -z "$INTEGREAT_CMS_INSTALLED" ]]; then
        echo "Checking if Integreat CMS is installed..." | print_info
        # Check if script was invoked with sudo
        if [[ $(id -u) == 0 ]] && [[ -n "$SUDO_USER" ]]; then
            # overwrite $HOME directory in case script was called with sudo but without the -E flag
            HOME="$(bash -c "cd ~${SUDO_USER} && pwd")"
        fi
        # Check if virtual environment exists
        if [[ -f ".venv/bin/activate" ]]; then
            # Activate virtual environment
            # shellcheck disable=SC1091
            source .venv/bin/activate
        else
            echo -e "The virtual environment for this project is missing. Please install it with:\n"  | print_error
            echo -e "\t$(dirname "${BASH_SOURCE[0]}")/install.sh\n" | print_bold
            exit 1
        fi
        # Check if integreat-cms-cli is available in virtual environment
        if [[ ! -x "$(env bash -c "command -v integreat-cms-cli")" ]]; then
            echo -e "The Integreat CMS is not installed. Please install it with:\n"  | print_error
            echo -e "\t$(dirname "${BASH_SOURCE[0]}")/install.sh\n" | print_bold
            exit 1
        fi
        echo "✔ Integreat CMS is installed" | print_success
        INTEGREAT_CMS_INSTALLED=1
        export INTEGREAT_CMS_INSTALLED
        # Check if script is running in CircleCI context and set DEBUG=True if not
        if [[ -z "$CIRCLECI" ]]; then
            # Set debug mode for
            INTEGREAT_CMS_DEBUG=1
            export INTEGREAT_CMS_DEBUG
            # Set dummy FCM key to test functionality
            if [[ -z "${INTEGREAT_CMS_FCM_KEY}" ]]; then
                INTEGREAT_CMS_FCM_KEY="dummy"
                export INTEGREAT_CMS_FCM_KEY
            fi
        fi
    fi
}

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
            sudo -u "$SUDO_USER" -E --preserve-env=PATH env "$@"
        fi
    else
        # If user already has low privileges, just call the given command(s)
        env "$@"
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
        echo "The script ${SCRIPT_NAME} needs root privileges to connect to the docker daemon. It will automatically be restarted with sudo." | print_warning
        # Call this script again as root (pass -E because we want the user's environment, not root's)
        sudo --preserve-env=HOME,PATH env "${SCRIPT_PATH}" "${SCRIPT_ARGS[@]}"
        # Exit with code of subprocess
        exit $?
    elif [[ -z "$SUDO_USER" ]]; then
        echo "Please do not run ${SCRIPT_NAME} as root user, use sudo instead." | print_error
        exit 1
    fi
}

# This function makes sure the script has the permission to interact with the docker daemon
function ensure_docker_permission {
    ERROR_MSG="Please start either a local PostgreSQL database server or start the docker daemon so a database docker container can be created."
    # Check if script runs as root
    if [[ $(id -u) == 0 ]]; then
        # Make sure it was invoked with sudo
        if [[ -z "$SUDO_USER" ]]; then
            echo "Please do not run ${SCRIPT_NAME} as root user, use sudo instead." | print_error
            exit 1
        fi
        # Check if docker socket is also available with lower permissions
        if sudo -u "$SUDO_USER" docker ps &> /dev/null; then
            # If command is available to the unprivileged user, ensure we don't run with higher privileges than necessary
            ensure_not_root
        elif ! docker ps &> /dev/null; then
            # If the command fails for root, we assume the docker daemon isn't running
            echo "${ERROR_MSG}" | print_error
            exit 1
        fi
    else
        # Check if docker socket is not available
        if ! docker ps &> /dev/null; then
            # Check if it's available with sudo
            if sudo docker ps &> /dev/null; then
                # If the command fails normally, but succeeds with sudo, require the permissions from now on
                ensure_root
            else
                # If the command still fails with sudo, we assume the docker daemon isn't running
                echo "${ERROR_MSG}" | print_error
                exit 1
            fi
        fi
    fi
}

# This function migrates the database
function migrate_database {
    # Check for the variable DATABASE_MIGRATED to prevent multiple subsequent migration commands
    if [[ -z "$DATABASE_MIGRATED" ]]; then
        echo "Migrating database..." | print_info
        # Make sure the migrations directory exists
        deescalate_privileges mkdir -pv "${PACKAGE_DIR}/cms/migrations"
        deescalate_privileges touch "${PACKAGE_DIR}/cms/migrations/__init__.py"
        # Generate migration files
        deescalate_privileges integreat-cms-cli makemigrations --verbosity "${SCRIPT_VERBOSITY}"
        # Execute migrations
        deescalate_privileges integreat-cms-cli migrate --verbosity "${SCRIPT_VERBOSITY}"
        echo "✔ Finished database migrations" | print_success
        DATABASE_MIGRATED=1
    fi
}

# This function waits for the docker database container
function wait_for_docker_container {
    # Wait until container is ready and accepts database connections
    until docker exec -it "${DOCKER_CONTAINER_NAME}" psql -U integreat -d integreat -c "select 1" > /dev/null 2>&1; do
        sleep 0.1
    done
}

# This function creates a new postgres database docker container
function create_docker_container {
    echo "Creating new PostgreSQL database docker container..." | print_info
    mkdir -p "${BASE_DIR}/.postgres"
    # Run new container
    docker run -d --name "${DOCKER_CONTAINER_NAME}" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "${BASE_DIR}/.postgres:/var/lib/postgresql" -p 5433:5432 postgres > /dev/null
    wait_for_docker_container
    echo "✔ Created database container" | print_success
    # Set up exit trap to stop docker container when script ends
    cleanup_docker_container
}

# This function starts an existing postgres database docker container
function start_docker_container {
    echo "Starting existing PostgreSQL database Docker container..." | print_info
    # Start the existing container
    docker start "${DOCKER_CONTAINER_NAME}" > /dev/null
    wait_for_docker_container
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
    # Make sure script has the permission to run docker
    ensure_docker_permission
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
    if nc -z localhost 5432; then
        ensure_not_root
        echo "✔ Running PostgreSQL database detected" | print_success
        # Migrate database
        migrate_database

        # Set default settings for other dev tools, e.g. testing
        export DJANGO_SETTINGS_MODULE="integreat_cms.core.settings"
    else
        # Set docker settings
        export DJANGO_SETTINGS_MODULE="integreat_cms.core.docker_settings"
        # Make sure a docker container is up and running
        ensure_docker_container_running
    fi
}

# This function sets the correct environment variables for the local Redis cache
function configure_redis_cache {
    # Check if local Redis server is running
    echo "Checking if local Redis server is running..." | print_info
    if nc -z localhost 6379; then
        # Enable redis cache if redis server is running
        export INTEGREAT_CMS_REDIS_CACHE=1
        # Check if enhanced connection via unix socket is available (write the location into $REDIS_SOCKET_LOCATION)
        if [[ -f "$REDIS_SOCKET_LOCATION" ]]; then
            # Set location of redis unix socket
            INTEGREAT_CMS_REDIS_UNIX_SOCKET=$(cat "$REDIS_SOCKET_LOCATION")
            export INTEGREAT_CMS_REDIS_UNIX_SOCKET
            echo "✔ Running Redis server on socket $INTEGREAT_CMS_REDIS_UNIX_SOCKET detected. Caching enabled." | print_success
        else
            echo "✔ Running Redis server on port 6379 detected. Caching enabled." | print_success
        fi
    else
        echo "❌No Redis server detected. Falling back to local-memory cache." | print_warning
    fi
}

# This function shows a success message once the Integreat development server is running
function listen_for_devserver {
    until nc -z localhost "$INTEGREAT_CMS_PORT"; do sleep 0.1; done
    echo "✔ Started Integreat CMS at http://localhost:${INTEGREAT_CMS_PORT}" | print_success
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

# This function applies different sed replacements to make sure the matched lines from grep are aligned and colored
function format_grep_output {
    while read -r line; do
        echo "$line" | sed --regexp-extended \
            -e "s/^([0-9])([:-])(.*)/\1\2      \3/"         `# Pad line numbers with 1 digit` \
            -e "s/^([0-9]{2})([:-])(.*)/\1\2     \3/"       `# Pad line numbers with 2 digits` \
            -e "s/^([0-9]{3})([:-])(.*)/\1\2    \3/"        `# Pad line numbers with 3 digits` \
            -e "s/^([0-9]{4})([:-])(.*)/\1\2   \3/"         `# Pad line numbers with 4 digits` \
            -e "s/^([0-9]{5})([:-])(.*)/\1\2  \3/"          `# Pad line numbers with 5 digits` \
            -e "s/^([0-9]+):(.*)/\x1b[1;31m\1\2\x1b[0;39m/" `# Make matched line red` \
            -e "s/^([0-9]+)-(.*)/\1\2/"                     `# Remove dash of unmatched line`
    done
}
