[![CircleCI](https://circleci.com/gh/Integreat/cms-django.svg?style=shield)](https://circleci.com/gh/Integreat/cms-django)
[![Pylint](https://img.shields.io/badge/pylint-10.00-brightgreen)](https://www.pylint.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

# Integreat Django CMS

This project aims to develop a content management system tailored to the needs of municipalities to provide multilingual local information.
Its goal is to be easy to use and easy to maintain over a long time.
This project uses Python3.7 and Django 2.2 and is supposed to run on Ubuntu 18.04.

## TL;DR

### Prerequisites

Following packages are required before installing the project (install them with your package manager):

* npm
* python3.7 (Debian-based distributions) / python37 (Arch-based distributions)
* python3.7-dev (only on Ubuntu)
* python3-pip (Debian-based distributions) / python-pip (Arch-based distributions)
* pipenv for python3 (if no recent version is packaged for your distro, use `pip3 install pipenv --user`)
* gettext to use the translation features
* Either postgresql **or** docker to run a local database server

### Installation

````
git clone git@github.com:Integreat/cms-django.git
cd cms-django
./dev-tools/install.sh
````

### Run development server

````
./dev-tools/run.sh
````

* Go to your browser and open the URL `http://localhost:8000`
* Default user is "root" with password "root1234".

## Documentation

For detailed instructions, tutorials and the source code reference have a look at our great documentation:

<p align="center">:notebook: https://integreat.github.io/cms-django/</p>
