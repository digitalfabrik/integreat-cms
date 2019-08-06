#!/bin/bash

# Start Postgres Docker container
if [ ! "$(docker ps -q -f name=integreat_django_postgres)" ]; then
    if [ "$(docker ps -aq -f status=exited -f name=integreat_django_postgres)" ]; then
        # Start the existing container
        docker start integreat_django_postgres
    else    
        # Run new container
        docker run --name "integreat_django_postgres" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "$(pwd)/.postgres:/var/lib/postgresql" -p 5433:5432 postgres &
    fi
fi

# Start Integreat CMS
cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate
integreat-cms runserver localhost:8000 --settings=backend.docker_settings

# Stop the postgres database docker container
docker stop integreat_django_postgres
