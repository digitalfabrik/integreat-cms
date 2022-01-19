#!/bin/bash

# This script can be used to prune the complete postgres database.
# It stops and removes the docker container and removes all database-related directories.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Check if local postgres server is running
if nc -w1 localhost 5432; then

    echo "Please delete and re-create your database manually, typically like this:

    user@host$ su postgres
    postgres@host$ psql

    > DROP DATABASE integreat;
    > CREATE DATABASE integreat;
" | print_info

else

    # Check if docker is installed
    if command -v docker > /dev/null; then

        # Make sure script has the permission to remove the .postgres directory owned by root (even if user is in docker group)
        ensure_root

        # Check if docker socket is available
        if docker ps > /dev/null; then
            # Check if postgres container is running
            if [ "$(docker ps -q -f name="${DOCKER_CONTAINER_NAME}")" ]; then
                # Stop Postgres Docker container
                stop_docker_container
            fi
            # Check if a stopped database container exists
            if [ "$(docker ps -aq -f status=exited -f name="${DOCKER_CONTAINER_NAME}")" ]; then
                # Remove Postgres Docker container
                docker rm "${DOCKER_CONTAINER_NAME}" > /dev/null
                echo "Removed database container" | print_info
            fi
        fi

        # Remove database directory
        rm -rfv "${BASE_DIR:?}/.postgres"
        echo "Removed database contents" | print_info

    fi

fi

# Remove media files (because they are no longer usable without the corresponding database entries)
rm -rfv "${PACKAGE_DIR:?}/media"
echo "Removed media files" | print_info
