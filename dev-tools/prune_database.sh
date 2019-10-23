#!/bin/bash

# This script can be used to prune the complete postgres database.
# It stops and removes the docker container and removes all database-related directories.

# Check if docker is installed and docker socket is available
if [ -x "$(command -v docker)" ] && docker ps > /dev/null 2>&1; then
    # Check if postgres container is running
    if [ "$(docker ps -q -f name=integreat_django_postgres)" ]; then
        # Stop Postgres Docker container
        docker stop integreat_django_postgres
    fi
    # Check if a stopped database container exists
    if [ "$(docker ps -aq -f status=exited -f name=integreat_django_postgres)" ]; then
        # Remove Postgres Docker container
        docker rm integreat_django_postgres
    fi
fi

# Remove all database related files
cd $(dirname "$BASH_SOURCE")/..
rm -rfv .postgres
rm -rfv backend/cms/migrations
