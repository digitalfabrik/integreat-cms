# Integreat Django CMS
This project aims to develop a content management system tailored to the needs of municipalities to provide multilingual local information. Its goal is to be easy to use and easy to maintain over a long time. This project uses Python3 and Django 2.2 and is supposed to run on Ubuntu 18.04.

## TL;DR

### Requirements
Following packages are required for running the project (Install them with your package manager):
* git
* npm
* python3.7
* python3-pip
* python3-pipenv
* python3.7-dev (only on Ubuntu)
* postgresql *OR* docker
* GNU gettext tools (to make use of the internationalization feature)

### Installation
````
git clone git@github.com:Integreat/cms-django.git
cd cms-django
./dev-tools/install.sh              # install venv and integreat-cms
````
### Running
````
./dev-tools/run.sh                  # start database and integreat-cms
````
* Go to your browser and open the URL `http://localhost:8000`
* Default user is "root" with password "root1234".
  * If you not use docker as database host you may need to [load sample data](#4.-Initial-test-data)

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
pipenv shell
```
Otherwise python dependency modules inside the venv can not be identified.

### 2. Internationalization (i18n)
This dev tool is a shortcut for all translation tasks:
```
./dev-tools/translate.sh
```
If you run into merge/rebase conflicts inside the translation file, use:
```
./dev-tools/resolve_translation_conflicts.sh
```
Alternatively, you can manage the translations manually.
After you changed translated texts in the code, rebuild the .mo file with the following command:
```
integreat-cms makemessages -l de
```
To make use of the translations in the backend, compile the django.po file as follows:
```
integreat-cms compilemessages
```
If you are using a virtual python environment, be sure to use the ´--exclude´ parameter or execute this command in the backend or cms directory, otherwise all the translation files in your venv will be compiled, too.

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
* Adjust database credentials to the one provided by your local environment in `src/backend/settings.py`

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
* If you didn't use the `dev-tools/run.sh`-script in step 2.1,  fire up the CMS (If port 8000 is already in use, you might use another one):
```
integreat-cms runserver localhost:8000
```

* Go to your browser and open the URL `http://localhost:8000`
* Default user is "root" with password "root1234".

You may need to activate the virtual environment explicitly via `pipenv shell`.

### 6. Testing
Run tests: `./dev-tools/test.sh`
Run tests with code coverage report generation: `./dev-tools/test_cov.sh`

### 7. Code quality
To make sure your code matches the repository's quality standards, run pylint as follows:
```
./dev-tools/pylint.sh
```

### 8. Developer Documentation
Required syntax of docstrings ([more information here](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html)):
```
"""
[Summary]

:param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
:type [ParamName]: [ParamType](, optional)
...
:raises [ErrorType]: [ErrorDescription]
...
:return: [ReturnDescription]
:rtype: [ReturnType]
"""
```

### 8. Add/Update dependencies
If you added new dependencies to `setup.py` or want to upgrade the versions of installed pip & npm dependencies, execute
```
./dev-tools/update_dependencies.sh
```
to make sure the dependency lock files are updated.

If you change models, functions or docstrings, make sure to update the corresponding developer documentation:
```
./dev-tools/generate_documentation.sh
```
This scans the source code for changed definitions and docstrings, generates intermediate .rst files and compiles them to the html documentation in /docs.

## Miscellaneous
* Keep in mind that we are using Python 3.7, so use `python3` (Ubuntu: `python3.7`, Arch Linux: `python37`) and `pip3` with any command
* Access the Postgres database running in Docker container: `docker exec -it integreat_django_postgres psql -U integreat`
* To ensure that you do not accidentally push your changes in `settings.py`, you can ignore the file locally via `git update-index --assume-unchanged ./backend/backend/settings.py`
* Delete the database to start over again: `./dev-tools/prune_database.sh`
* Create root superuser: `./dev-tools/create_superuser.sh`

## Complete reset of the environment
As the project is still in an early stage with a lot of changes to the database structure from different contributors, it can come in handy to reset the project completely. To do so, follow the this steps:
1. Stop Django by pressing STRG+C
4. Run `./dev-tools/prune_database.sh` 
(If some of the files/directories are not accessible, delete them manually with `sudo rm -rf DIRECTORY/FILE`

After this steps, the project should be reset completely. Follow the install instructions to keep it up running again.

## Packaging and installing on Ubuntu 18.04
Packaging for Debian can be done with setuptools.
```
$ pip3 install stdeb
$ python3 setup.py --command-packages=stdeb.command bdist_deb
```
The project requires the package python3-django-widget-tweaks which has to be built manually:
````
$ git clone git@github.com:jazzband/django-widget-tweaks.git
$ cd django-widget-tweaks
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
