# Integreat Django CMS
This project aims to develop a content management system tailored to the needs of municipalities to provide multilingual local information. It aims at being easy to use and easy to maintain over a long time. This project uses Python3 and Django 1.11 and aims at being run on a Ubuntu 18.04.

## Setup a local development environment
To run the project locally you can either install as a package (Ubuntu, openSUSE) or you can run in local Python3 **virtualenv**, and also in a Docker container. Using **virtualenv** is the recommended way for setting up a local development environment.

First of all, clone the project:
````
git clone git@github.com:Integreat/cms-django.git
cd cms-django
````

### Setup the database
You can run Postgres either on your local machine or in a Docker container.

* Install Postgres on your machine ([Tutorial for Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04))
* Run Postgres in a Docker container: `./dev-tools/start_db_docker.sh`

### virtualenv
1. Run `./install-venv.sh`
2. If you have installed Postgres on your machine, you may have to adjust database credentials in `backend/backend/settings.py`
3. Do the database migrations: `integreat-cms migrate`
4. Create the initial superuser: `integreat-cms createsuperuser`
5. Fire up the CMS: `integreat-cms runserver localhost:8000`
6. Go to your browser and open the URL `http://localhost:8000`

You may need to activate the `virtualenv` explicitly via `source .venv/bin/activate`.

## Development
### Migrations
After changing a models you have to migrate via `./dev-tools/migrate.sh`

### i18n
To make use of the translated backend, compile the django.po file as follows:

`django-admin compilemessages`

If you are using a virtual python environment, be sure to use the ´--exclude´ parameter or execute this command in the backend or cms directory, otherwise all the translation files in your venv will be compiled, too.

### Testing
Run Django unittest: `integreat-cms test cms/`

### Miscellaneous
* Keep in mind that we are using Python 3.x, so use `python3` and `pip3` with any command
* Access the Postgres database running in Docker container: `docker exec -it integreat_django_postgres psql -U integreat`
* Too ensure that you do not accidentally push your changes in `settings.py`, you can ignore the file locally via `git update-index --assume-unchanged ./backend/backend/settings.py`
* Delete the database to start over again: `dev-tools/prune_database.sh`
* Create superuser: `dev-tools/create_superuser.sh`

## Packaging and installing on Ubuntu 18.04
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