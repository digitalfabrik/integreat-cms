#!/bin/sh

docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms createsuperuser --username root --email ''"
