#!/bin/bash

# This script can be used to start the cms together with a postgres database docker container.
# It also includes generating translation files and applying migrations after the docker container is started for the first time.

# Make sure Webpack background process is terminated when script ends
trap "exit" INT TERM ERR
trap "kill 0" EXIT
KILL_TRAP=1

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Require that integreat-cms is installed
require_installed

# Initialize the Redis cache settings by setting the correct environment variables
configure_redis_cache

# Require that a database server is up and running. Place this command at the beginning because it might require the restart of the script with higher privileges.
require_database

# Skip migrations and translations if --fast option is given
if [[ "$*" != *"--fast"* ]]; then
    # Migrate database
    migrate_database
    # Updating translation file
    deescalate_privileges bash "${DEV_TOOL_DIR}/translate.sh"
fi

# Remove any stale webpack-stats.json from a previous run so the gate
# below cannot be fooled into proceeding while webpack is still building
# (e.g. into reading a leftover "error" or "done" status from before).
rm -f "${PACKAGE_DIR}/webpack-stats.json"

# Check if compiled webpack output exists
if [[ -z $(compgen -G "${PACKAGE_DIR}/static/dist/main.*.js") ]]; then
    echo -e "The compiled static files do not exist yet, therefore the start of the Django dev server will be delayed until the initial WebPack build is completed." | print_warning
fi

# Starting WebPack dev server in background
echo -e "Starting WebPack dev server in background..." | print_info | print_prefix "webpack" 36
deescalate_privileges npm run dev 2>&1 | print_prefix "webpack" 36 &

# Wait for the initial WebPack dev build to finish writing webpack-stats.json.
# We block on the actual ``status`` field rather than the presence of a dist
# file, because webpack only ``clean``s the dist directory just before emit;
# a leftover ``main.*.js`` from a prior good build would otherwise let Django
# start while webpack is still compiling, racing into a 500.
WEBPACK_STATS_FILE="${PACKAGE_DIR}/webpack-stats.json"
WEBPACK_WAIT_DEADLINE=$(( SECONDS + 180 ))
while :; do
    WEBPACK_STATUS=$(python3 -c "
import json, sys
try:
    with open('${WEBPACK_STATS_FILE}', encoding='utf-8') as f:
        print(json.load(f).get('status', ''))
except (OSError, ValueError):
    pass
" 2>/dev/null || true)
    if [[ "${WEBPACK_STATUS}" == "done" ]]; then
        break
    fi
    if [[ "${WEBPACK_STATUS}" == "error" ]]; then
        echo -e "Initial WebPack build failed; see the [webpack] log above for details." | print_error
        exit 1
    fi
    if (( SECONDS > WEBPACK_WAIT_DEADLINE )); then
        echo -e "Initial WebPack build did not complete within 180s." | print_error
        exit 1
    fi
    sleep 1
done

# Show success message once dev server is up
listen_for_devserver &

# Run Celery worker process
if [ "$INTEGREAT_CMS_REDIS_CACHE" == "1" ]; then
  deescalate_privileges celery --app integreat_cms.integreat_celery worker --loglevel INFO -B --concurrency=4 --queues default,celery,chat,statistics &
fi

# Start Integreat CMS development webserver
deescalate_privileges integreat-cms-cli runserver "localhost:${INTEGREAT_CMS_PORT}"
