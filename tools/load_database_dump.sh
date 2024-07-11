#!/bin/bash

# This script can be used to load downloaded database dump.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"
require_installed

SQL_DATA_PATH=$1

bash "${DEV_TOOL_DIR}/prune_database.sh"

docker run -d --name "${DOCKER_CONTAINER_NAME}" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "${BASE_DIR}/.postgres:/var/lib/postgresql" -p "${INTEGREAT_CMS_DOCKER_LISTEN_PORT}":"${INTEGREAT_CMS_DB_PORT}" postgres > /dev/null
wait_for_docker_container

docker exec -i "${DOCKER_CONTAINER_NAME}" psql -U integreat < "${SQL_DATA_PATH}"

bash "${DEV_TOOL_DIR}/migrate.sh"

bash "${DEV_TOOL_DIR}/create_superuser.sh"

echo -e "✔ Done😻" | print_success
echo -e "Use ./tools/run.sh as always" | print_info
