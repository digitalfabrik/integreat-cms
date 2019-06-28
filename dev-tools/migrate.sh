#!/bin/sh

docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms makemigrations cms"
docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms migrate"
docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms loaddata backend/cms/fixtures/roles.json"
