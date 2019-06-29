#!/bin/sh

# Change connection string
sed -i 's/5432/5433/g' ./backend/backend/settings.py

# Start Postgres Docker container
if [ ! "$(docker ps -q -f name='integreat_django_postgres')" ]; then
    if [ "$(docker ps -aq -f status=exited -f name='integreat_django_postgres')" ]; then
        # Start the existing container
        docker start integreat_django_postgres
    else    
        # Run new container
        docker run --name "integreat_django_postgres" -e "POSTGRES_USER=integreat" -e "POSTGRES_PASSWORD=password" -e "POSTGRES_DB=integreat" -v "$(pwd)/.postgres:/var/lib/postgresql" -p 5433:5432 postgres
    fi
fi