#!/bin/bash

# This script can be used to generate migrations and applying them afterwards.
# It can be used with the postgres docker container as well as a standalone installation.

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate
# Set docker settings environment variable if postgres container is running

export DJANGO_SETTINGS_MODULE=backend.settings
if [ -x "$(command -v docker)" ]; then
    docker ps -q -f name=integreat_django_postgres
    if [[ $? == 0 ]]; then
        export DJANGO_SETTINGS_MODULE=backend.docker_settings
    fi
fi

integreat-cms makemigrations cms
integreat-cms migrate
integreat-cms loaddata backend/cms/fixtures/roles.json
