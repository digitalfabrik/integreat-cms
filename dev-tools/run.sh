#!/bin/bash

# This script can be used to start the cms together with a postgres database docker container.
# It also includes generating translation files and applying migrations after the docker container is started for the first time.

# Activate venv
cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate

# Re-generating translation file and compile it
./dev-tools/translate.sh

# Check if docker is installed and docker socket is available
if [ -x "$(command -v docker)" ] && docker ps > /dev/null 2>&1; then
    export DJANGO_SETTINGS_MODULE=backend.docker_settings
    # Check if postgres database container is already running
    if [ ! "$(docker ps -q -f name=integreat_django_postgres)" ]; then
        # Check if stopped container is available
        if [ "$(docker ps -aq -f status=exited -f name=integreat_django_postgres)" ]; then
            # Start the existing container
            docker start integreat_django_postgres > /dev/null 2>&1
        else
            # Run new container
            docker run -d --name "integreat_django_postgres" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "$(pwd)/.postgres:/var/lib/postgresql" -p 5433:5432 postgres > /dev/null 2>&1
            echo -n "Waiting for postgres database container to be ready..."
            until docker exec -it integreat_django_postgres psql -U integreat -d integreat -c "select 1" > /dev/null 2>&1; do
              sleep 0.1
              echo -n "."
            done
            echo ""
            # Migrate database
            ./dev-tools/migrate.sh
            # Import test data
            ./dev-tools/loadtestdata.sh
        fi
    fi
fi

# Migrate database
./dev-tools/migrate.sh

# Start Integreat CMS
integreat-cms runserver localhost:8000

if [ -x "$(command -v docker)" ] && docker ps > /dev/null 2>&1; then
    # Stop the postgres database docker container
    docker stop integreat_django_postgres
fi
