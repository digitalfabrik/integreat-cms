#!/bin/bash

# This script can be used to prune the complete postgres database.
# It stops and removes the docker container and removes all database-related directories.

# Stop Postgres Docker container
if [ "$(docker ps -q -f name=integreat_django_postgres)" ]; then
    docker stop integreat_django_postgres
fi

# Remove Postgres Docker container
if [ "$(docker ps -aq -f status=exited -f name=integreat_django_postgres)" ]; then
    docker rm integreat_django_postgres
fi

# Remove all database related files
cd $(dirname "$BASH_SOURCE")/..
rm -rfv .postgres
rm -rfv backend/cms/migrations
