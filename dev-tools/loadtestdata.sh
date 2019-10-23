#!/bin/bash

# This script imports test data into the database.

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate

# Check if docker is installed and docker socket is available
if [ -x "$(command -v docker)" ] && docker ps > /dev/null 2>&1; then
    export DJANGO_SETTINGS_MODULE=backend.docker_settings
fi

# Create new dummy user if not exists (otherwise the import might fail due to constraints)
integreat-cms createsuperuser --noinput  --username 'dummy_user' --email 'test@test.test' > /dev/null 2>&1
integreat-cms loaddata backend/cms/fixtures/test_data.json
integreat-cms loaddata backend/cms/fixtures/extra_templates.json
