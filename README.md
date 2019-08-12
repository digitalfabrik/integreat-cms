# Integreat Django CMS
This project aims to develop a content management system tailored to the needs of municipalities to provide multilingual local information. Its goal is to be easy to use and easy to maintain over a long time. This project uses Python3 and Django 1.11 and is supposed to run on Ubuntu 18.04.

## TL;DR
### Installation
````
git clone git@github.com:Integreat/cms-django.git
cd cms-django
./dev-tools/install.sh              # install venv and integreat-cms
````
### Running
````
./dev-tools/run.sh                  # start database and integreat-cms
./dev-tools/migrate.sh              # migrate database
./dev-tools/create_superuser.sh     # create root user for cms
````

## Detailed instructions

First of all, clone the project:
````
git clone git@github.com:Integreat/cms-django.git
cd cms-django
````

### 1. Virtual environment
Install a python virtual environment and setup integreat-cms in this venv:
```
./dev-tools/install.sh
```
If you want to use the Django command line instructions with `integreat-cms` (instead of our dev-tools), you have to activate it:
```
source .venv/bin/activate
```
Otherwise python dependency modules inside the venv can not be identified.


### 2. Internationalization (i18n)
To make use of the translated backend, compile the django.po file as follows:

```
integreat-cms compilemessages
```

If you are using a virtual python environment, be sure to use the ´--exclude´ parameter or execute this command in the backend or cms directory, otherwise all the translation files in your venv will be compiled, too.

After you changed translated texts in the code, rebuild the .mo file with the following command:
```
integreat-cms makemessages -a
```

### 2. Postgres database
You can run Postgres either in a Docker container or on your local server.

####  2.1. Docker (recommended)
Run Postgres in our provided Docker container and start the `integreat-cms` local server subsequently:
```
./dev-tools/run.sh
```
On the first run, this will also migrate the database and populate it with initial test data.

#### 2.2. Manually install postgres
Alternatively,
* Install Postgres on your machine ([Tutorial for Ubuntu 18.04](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04))
* Adjust database credentials to the one provided by your local environment in `backend/backend/settings.py`

### 3. Database migrations
While the database is running, migrate it:
```
./dev-tools/migrate.sh
```

### 4. Initial test data
To import initial test data into the database, execute:
```
./dev-tools/loadtestdata.sh
```

### 5. Running
* While the database is running, create a first superuser:
```
integreat-cms createsuperuser
```
* If you didn't use the `dev-tools/run.sh`-script in step 2.1,  fire up the CMS (If port 8000 is already in use, you might use 5000):
```
integreat-cms runserver localhost:8000
```

* Go to your browser and open the URL `http://localhost:8000`

You may need to activate the `virtualenv` explicitly via `source .venv/bin/activate`.

### 6. Testing
Run Django unittest: `integreat-cms test cms/`

## Miscellaneous
* Keep in mind that we are using Python 3.x, so use `python3` and `pip3` with any command
* Access the Postgres database running in Docker container: `docker exec -it integreat_django_postgres psql -U integreat`
* To ensure that you do not accidentally push your changes in `settings.py`, you can ignore the file locally via `git update-index --assume-unchanged ./backend/backend/settings.py`
* Delete the database to start over again: `./dev-tools/prune_database.sh`
* Create root superuser without email-address: `./dev-tools/create_superuser.sh`

## Complete reset of the environment
As the project is still in an early stage with a lot of changes to the database structure from different contributors, it can come in handy to reset the project completely. To do so, follow the this steps:
1. Stop Django by pressing STRG+C
4. Run `./dev-tools/prune_database.sh` 
(If some of the files/directories are not accessible, delete them manually with `sudo rm -r DIRECTORY/FILE`

After this steps, the project should be reseted completely. Follow the install instructions to keep it up running again.

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
