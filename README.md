# Integreat Django CMS
This project aims to develop a content management system tailored to the needs of municipalities to provide multilingual local information. It aims at being easy to use and easy to maintain over a long time. This project uses Python3 and Django 1.11 and aims at being run on a Ubuntu 18.04.

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
8. Run Django unittest: `integreat-cms test cms/`

### Run CMS in Docker container
A docker-compose file is provided in the the repository. It will start one container with a PostgreSQL database and another one with the CMS.
* `docker-compose up`
* enter [http://localhost:8000](http://localhost:8000)
* as long as there is no standard SQL dump, you have to create your own user: `docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms createsuperuser"`

### Packaging and installing on Ubuntu 18.04
Packaging for Debian can be done with setuptools.
```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install stdeb
$ python3 setup.py --command-packages=stdeb.command bdist_deb
```
The project requires the package python3-django-widget-tweaks which has to be build manually:
````
$ git clone git@github.com:jazzband/django-widget-tweaks.git
$ cd django-widget-tweaks
$ python3 -m venv .venv
$ pip3 install stdeb
$ python3 setup.py --command-packages=stdeb.command bdist_deb
````
Then install both packages with gdebi:
````
# apt install gdebi postgresql
# gdebi django-widget-tweaks/deb_dist/python3-django-widget-tweaks_1.4.3-1_all.deb
# gebi cms-django/deb_dist/python3-integreat-cms_0.0.13-1_all.deb
````
In the end, create a PostgreSQL user and database and adjust the `/usr/lib/python3/dist-packages/backend/settings.py`.


### Troubleshooting
#### Cleaning up Docker environment
* stop all conntainers: `docker stop $(docker ps -a -q)`
* remove all images: `docker rmi $(docker images -a -q)`
* remove all volumes: `docker system prune`
#### Misc
* keep in mind that we are using Python 3.x, so use `python3` and `pip3` on your bash commands
* get a bash shell in the django container: `docker exec -it $(docker-compose ps -q django) bash`
* enter postgres container: `docker exec -it $(docker-compose ps -q postgres) psql -U"integreat" -d "integreat"`

### Migrations
* change models
* `docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms makemigrations [app]"`
* optional, if you want to inspect the corresponding SQL syntax: `docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms sqlmigrate [app] [number]"`
* `docker exec -it $(docker-compose ps -q django) bash -ic "integreat-cms migrate"`

### Docker clean up
* `docker stop $(docker ps -a -q)`
* `docker rm $(docker ps -a -q)`
* remove all images: `docker rmi $(docker images -a -q)`
* remove all volumes: `docker volume prune`

### i18n
To make use of the translated backend, compile the django.po file as follows:

`django-admin compilemessages`

If you use a virtual python environment, be sure to use the ´--exclude´ parameter or execute this command in the backend or cms directory, otherwise all the translation files in your venv will be compiled, too.

