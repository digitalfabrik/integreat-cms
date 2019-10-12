#!/bin/bash

# This script imports test data into the database.

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

integreat-cms loaddata backend/cms/fixtures/test_data.json
integreat-cms loaddata backend/cms/fixtures/extra_templates.json
