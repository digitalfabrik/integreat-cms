[![CircleCI](https://circleci.com/gh/Integreat/integreat-cms.svg?style=shield)](https://circleci.com/gh/Integreat/integreat-cms)
[![Pylint](https://img.shields.io/badge/pylint-10.00-brightgreen)](https://www.pylint.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Integreat Django CMS

[![Logo](.github/logo.png) Integreat - The mobile guide for newcomers.](https://integreat-app.de/en/) Multilingual. Offline. Open Source.

This content management system helps local integration experts to provide multilingual information for newcomers.

## TL;DR

### Prerequisites

Following packages are required before installing the project (install them with your package manager):

* npm version 7 or higher
* nodejs version 12 or version 14 or higher
* python3.7 (Debian-based distributions) / python37 (Arch-based distributions)
* python3.7-dev (only on Ubuntu)
* python3-pip (Debian-based distributions) / python-pip (Arch-based distributions)
* pipenv for python3 (if no recent version is packaged for your distro, use `pip3 install pipenv --user`)
* gettext to use the translation features
* Either postgresql **or** docker to run a local database server

### Installation

````
git clone git@github.com:Integreat/integreat-cms.git
cd integreat-cms
./dev-tools/install.sh
````

### Run development server

````
./dev-tools/run.sh
````

* Go to your browser and open the URL `http://localhost:8000`
* Default user is "root" with password "root1234".

### Run production server
1. Set up an [Apache2 server with mod_wsgi](https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/modwsgi/). You can use the `example-configs/apache2-integreat-vhost.conf`.
2. Set the following environment variables in the Apache2 config to ensure a safe service:
  * DJANGO_SECRET_KEY
  * DJANGO_DEBUG
  * DJANGO_WEBAPP_URL
  * DJANGO_BASE_URL
  * DJANGO_DB_HOST
  * DJANGO_DB_PORT
  * DJANGO_DB_USER
  * DJANGO_DB_NAME
  * DJANGO_DB_PASSWORD
  * DJANGO_STATIC_ROOT
  * DJANGO_MEDIA_ROOT
3. Clone this repo into `/opt/`. Edit the `settings.py`.
4. Create a virtual environment: `cd /opt/integreat-cms && python3 -m venv .venv && source .venv/bin/activate`
5. Use setuptools to install: `python3 setup.py develop`. It is also possible to use the `install` parameter, but this requires changes to the `wsgi.py` path in the Apache2 config.
6. Set up a PostgreSQL database and run the migrations: `integreat-cms-cli migrate`
7. Collect static files: `integreat-cms-cli collectstatic`

## Documentation

For detailed instructions, tutorials and the source code reference have a look at our great documentation:

<p align="center">:notebook: https://integreat.github.io/integreat-cms/</p>
