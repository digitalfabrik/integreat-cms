#!/bin/bash

# This script can be used to generate migrations and applying them afterwards.
# It can be used with the postgres docker container as well as a standalone installation.

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate

# Check if docker is installed and docker socket is available
if [ -x "$(command -v docker)" ] && docker ps > /dev/null 2>&1; then
    # Check if postgres container is running
    if [ ! "$(docker ps -q -f name=integreat_django_postgres)" ]; then
        echo "The postgres database docker container is not running." >&2
        exit 1
    fi
    # Set docker settings environment variable
    export DJANGO_SETTINGS_MODULE=backend.docker_settings
fi

integreat-cms makemigrations cms
integreat-cms migrate
integreat-cms loaddata backend/cms/fixtures/roles.json
