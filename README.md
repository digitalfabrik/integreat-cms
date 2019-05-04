# Integreat Django CMS
## Development
There are several ways to run this project locally: install as a package (Ubuntu, openSUSE), run in local Python3 venv, and also in a Docker container. Each method is detailed below.

To get started, run
````
git clone git@github.com:Integreat/cms-django.git
cd cms-django
````

### Development Tools

- Delete docker environment to start over again: `dev-tools/prune_docker.sh`
  (be careful: This will delete all your other docker images as well)
- Delete database to start over again: `dev-tools/prune_database.sh`
- Migrate database: `dev-tools/migrate.sh`
- Create superuser: `dev-tools/create_superuser.sh`

### Run CMS in Python3 venv
1. Install a local PostgreSQL server, for example with `apt install postgresql` and create a database and database user with the name `integreat`.
2. Run `./install-venv.sh`
3. Open the `backend/backend/settings.py` and adjust the database credentials. Also change the hostname to `localhost`.
4. Do the database migrations: `integreat-cms migrate`
5. Create the initial superuser: `integreat-cms createsuperuser`
6. Fire up the CMS: `integreat-cms runserver localhost:8000`
7. Go to your browser and open the URL `http://localhost:8000`

### Run CMS in Docker container
A docker-compose file is provided in the the repository. It will start one container with a PostgreSQL database and another one with the CMS.
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
