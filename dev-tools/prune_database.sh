#!/bin/bash

# This script can be used to prune the complete postgres database.
# It stops and removes the docker container and removes all database-related directories.

# Check if local postgres server is running
if nc -w1 localhost 5432; then

    echo "Please delete and re-create your database manually, typically like this:

    user@host$ su postgres
    postgres@host$ psql

    > DROP DATABASE integreat;
    > CREATE DATABASE integreat;
"

else

    # Check if docker is installed
    if command -v docker > /dev/null; then

        # Check if script is not running as root
        if ! [ $(id -u) = 0 ]; then
            echo "This script needs root privileges to connect to the docker deamon. It will be automatically restarted with sudo." >&2
            # Call this script again as root
            sudo $0
            # Exit with code of subprocess
            exit $?
        elif [ -z "$SUDO_USER" ]; then
            echo "Please do not run this script as your root user, use sudo instead." >&2
            exit 1
        fi

        # Check if docker socket is available
        if docker ps > /dev/null; then
            # Check if postgres container is running
            if [ "$(docker ps -q -f name=integreat_django_postgres)" ]; then
                # Stop Postgres Docker container
                docker stop integreat_django_postgres > /dev/null
            fi
            # Check if a stopped database container exists
            if [ "$(docker ps -aq -f status=exited -f name=integreat_django_postgres)" ]; then
                # Remove Postgres Docker container
                docker rm integreat_django_postgres > /dev/null
            fi
        fi

        # Remove database directory
        rm -rfv $(dirname "$BASH_SOURCE")/../.postgres

    fi

fi

# Remove migrations
rm -rfv $(dirname "$BASH_SOURCE")/../backend/cms/migrations
