# Integreat Django CMS
## Development
### Local development setup
* `docker-compose up`
* enter [http://localhost:8000](http://localhost:8000)
* as long as there is no standard SQL dump, you have to create your own user: `docker exec -it $(docker-compose ps -q django) bash -c "python3 manage.py createsuperuser"`

### Testing

## Production

## Miscellaneous
* keep in mind that we are using Python 3.x, so use `python3` and `pip3` on your bash commands
* get a bash shell in the django container: `docker exec -it $(docker-compose ps -q django) bash`
* enter postgres container: `docker exec -it $(docker-compose ps -q postgres) psql -U"integreat" -d "integreat"`

### Migrations
* change models
* `docker exec -it $(docker-compose ps -q django) bash -c "python3 manage.py makemigrations [app]"`
* optional, if you want to inspect the corresponding SQL syntax: `docker exec -it $(docker-compose ps -q django) bash -c "python3 manage.py sqlmigrate [app] [number]"`
* `docker exec -it $(docker-compose ps -q django) bash -c "python3 manage.py migrate"`

### pip dependencies
* freeze new installed dependencies via `docker exec -it $(docker-compose ps -q django) bash -c "pip3 freeze > requirements.txt"`
* install requirements via `docker exec -it $(docker-compose ps -q django) bash -c "pip3 install -r requirements.txt"`

### Docker clean up
* `docker stop $(docker ps -a -q)`
* `docker rm $(docker ps -a -q)`
* remove all images: `docker rmi $(docker images -a -q)`
* remove all volumes: `docker volume prune`

### i18n
To make use of the translated backend, compile the django.po file as follows:

`django-admin compilemessages`

If you use a virtual python environment, be sure to use the ´--exclude´ parameter or execute this command in the backend or cms directory, otherwise all the translation files in your venv will be compiled, too.
