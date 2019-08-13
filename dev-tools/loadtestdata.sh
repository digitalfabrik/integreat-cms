#!/bin/bash

# This script imports test data into the database.

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate
# Set docker settings environment variable if postgres container is running
if [ -x "$(command -v docker)" ] && [ "$(docker ps -q -f name=integreat_django_postgres)" ]; then
    export DJANGO_SETTINGS_MODULE=backend.docker_settings
fi
integreat-cms loaddata backend/cms/fixtures/test_data.json
