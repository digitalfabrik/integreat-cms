#!/bin/bash

# This script can be used to start the cms together with a postgres database docker container.
# It also includes generating translation files and applying migrations after the docker container is started for the first time.

# Make sure Webpack background process is terminated when script ends
trap "exit" INT TERM ERR
trap "kill 0" EXIT
KILL_TRAP=1

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Require that integreat-cms is installed
require_installed

# Require that a database server is up and running. Place this command at the beginning because it might require the restart of the script with higher privileges.
require_database

# Skip migrations and translations if --fast option is given
if [[ "$*" != *"--fast"* ]]; then
    # Migrate database
    migrate_database
    # Updating translation file
    deescalate_privileges bash "${DEV_TOOL_DIR}/translate.sh"
fi

# Check if compiled webpack output exists
if [[ ! -f "${BASE_DIR}/src/cms/static/main.js" ]]; then
    echo -e "The compiled static files do not exist yet, therefore the start of the Django dev server will be delayed until the initial WebPack build is completed." | print_warning
fi

# Starting WebPack dev server in background
echo -e "Starting WebPack dev server in background..." | print_info | print_prefix "webpack" 36
deescalate_privileges npm run dev 2>&1 | print_prefix "webpack" 36 &

# Waiting for initial WebPack dev build
compgen -G "${BASE_DIR}/src/cms/static/main.*.js" > /dev/null
while [[ $? -eq 1 ]]; do 
    sleep 1
    compgen -G "${BASE_DIR}/src/cms/static/main.*.js" > /dev/null
done

# Show success message once dev server is up
listen_for_devserver &

# Start Integreat CMS development webserver
deescalate_privileges pipenv run integreat-cms-cli runserver "localhost:${INTEGREAT_CMS_PORT}"
