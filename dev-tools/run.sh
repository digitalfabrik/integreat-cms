#!/bin/bash

# This script can be used to start the cms together with a postgres database docker container.
# It also includes generating translation files and applying migrations after the docker container is started for the first time.

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

# Check if nc (netcat) is installed
if [ ! -x "$(command -v nc)" ]; then
    echo "Netcat is not installed. Please install it manually and run this script again." >&2
    exit 1
fi

# Check if local postgres server is running
if nc -w1 localhost 5432; then

    # Check if script is running as root
    if [ $(id -u) = 0 ]; then
        # Check if script was invoked by the root user or with sudo
        if [ -z "$SUDO_USER" ]; then
            echo "Please do not execute run.sh as your root user." >&2
            exit 1
        else
            # Call this script again as the user who executed sudo
            sudo -u $SUDO_USER env PATH="$PATH" $0
            # Exit with code of subprocess
            exit $?
        fi
    fi

    cd $(dirname "$BASH_SOURCE")/..

    # Browserify revisions.js
    npx browserify src/cms/static/js/revisions.js -o src/cms/static/js/revisions_browserified.js -t [ babelify --presets [ @babel/preset-env ] ]

    # Re-generating translation file and compile it
    ./dev-tools/translate.sh

    # Migrate database
    ./dev-tools/migrate.sh

    # Start Integreat CMS
    pipenv run integreat-cms-cli tailwind start &
    pipenv run integreat-cms-cli runserver localhost:8000

else

    # Check if docker is not installed
    if ! command -v docker > /dev/null; then
        echo "In order to run the database, you need either a local postgres server or docker." >&2
        exit 1
    fi

    # Check if script is not running as root
    if ! [ $(id -u) = 0 ]; then
        echo "This script needs root privileges to connect to the docker deamon. It will be automatically restarted with sudo." >&2
        # Call this script again as root
        sudo env PATH="$PATH" $0
        # Exit with code of subprocess
        exit $?
    elif [ -z "$SUDO_USER" ]; then
        echo "Please do not run this script as your root user, use sudo instead." >&2
        exit 1
    fi

    # Check if docker socket is not available
    if ! docker ps > /dev/null; then
        exit 1
    fi

    cd $(dirname "$BASH_SOURCE")/..

    # Browserify revisions.js
    sudo -u $SUDO_USER env PATH="$PATH" npx browserify src/cms/static/js/revisions.js -o src/cms/static/js/revisions_browserified.js -t [ babelify --presets [ @babel/preset-env ] ]

    # Re-generating translation file and compile it
    sudo -u $SUDO_USER env PATH="$PATH" ./dev-tools/translate.sh

    # Check if postgres database container is already running
    if [ "$(docker ps -q -f name=integreat_django_postgres)" ]; then
        # Migrate database
        ./dev-tools/migrate.sh
    else
        # Check if stopped container is available
        if [ "$(docker ps -aq -f status=exited -f name=integreat_django_postgres)" ]; then
            # Start the existing container
            docker start integreat_django_postgres > /dev/null
            until docker exec -it integreat_django_postgres psql -U integreat -d integreat -c "select 1" > /dev/null 2>&1; do
              sleep 0.1
            done
            # Migrate database
            ./dev-tools/migrate.sh
        else
            # Run new container
            docker run -d --name "integreat_django_postgres" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "$(pwd)/.postgres:/var/lib/postgresql" -p 5433:5432 postgres > /dev/null
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

    # Start Integreat CMS
    sudo -u $SUDO_USER env PATH="$PATH" pipenv run integreat-cms-cli tailwind start &
    sudo -u $SUDO_USER env PATH="$PATH" pipenv run integreat-cms-cli runserver localhost:8000 --settings=backend.docker_settings

    # Stop the postgres database docker container
    docker stop integreat_django_postgres > /dev/null

fi
