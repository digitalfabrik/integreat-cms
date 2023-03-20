[![CircleCI](https://circleci.com/gh/digitalfabrik/integreat-cms.svg?style=shield)](https://circleci.com/gh/digitalfabrik/integreat-cms)
[![Pylint](https://img.shields.io/badge/pylint-10.00-brightgreen)](https://www.pylint.org/)
![Coverage](https://img.shields.io/codeclimate/coverage/digitalfabrik/integreat-cms)
[![PyPi](https://img.shields.io/pypi/v/integreat-cms.svg)](https://pypi.org/project/integreat-cms/)
[![Release Notes](https://img.shields.io/badge/%F0%9F%93%9C-release%20notes-blue)](https://digitalfabrik.github.io/integreat-cms/release-notes.html)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Integreat Django CMS

[![Logo](.github/logo.png) Integreat - The mobile guide for newcomers.](https://integreat-app.de/en/) Multilingual. Offline. Open Source.

This content management system helps local integration experts to provide multilingual information for newcomers.

## TL;DR

### Prerequisites

Following packages are required before installing the project (install them with your package manager):

* `npm` version 7 or later
* `nodejs` version 12 or later
* `python3` version 3.9 or later
* `python3-pip` (Debian-based distributions) / `python-pip` (Arch-based distributions)
* `python3-venv` (only on Debian-based distributions)
* `gettext` to use the translation features
* Either `postgresql` **or** `docker` to run a local database server

### Installation

````
git clone git@github.com:digitalfabrik/integreat-cms.git
cd integreat-cms
./tools/install.sh
````

### Run development server

````
./tools/run.sh
````

* Go to your browser and open the URL `http://localhost:8000`
* Default user is "root" with password "root1234".

## Documentation

For detailed instructions, tutorials and the source code reference have a look at our great documentation:

<p align="center">:notebook: https://digitalfabrik.github.io/integreat-cms/</p>

Alternatively, you can generate it yourself using the `tools/make_docs.sh` script.


## Project Architecture / Reference

- [Integreat CMS](integreat_cms): The main package of the integreat-cms with the following sub-packages:
	- [API](integreat_cms/api): This app provides wrapper functions around all API routes and classes mapping the cms models to API JSON responses.
	- [CMS](integreat_cms/cms): This app contains all database models, views, forms and templates forming the content management system for backend users.
	- [Core](integreat_cms/core): This is the project’s main app which contains all configuration files.
	- [Firebase API](firebase_api): This app provides wrapper functions around the Firebase API to send push notifications.
	- [GVZ API](integreat_cms/gvz_api): This app provides wrapper functions around our Gemeindeverzeichnis API to automatically import coordinates and region aliases.
	- [Nominatim API](nominatim_api): This app provides wrapper functions around our Nominatim API to automatically import region bounding boxes.
	- [Sitemap](integreat_cms/sitemap): This app dynamically generates a sitemap.xml for the webapp.
	- [SUMM.AI API](integreat_cms/summ_ai_api): This app provides wrapper functions around the SUMM.AI API for automatic translations into Easy German.
	- [XLIFF](integreat_cms/xliff): This app allows (de-)serialization of translations from/to XLIFF (XML Localization Interchange File Format) for standardised exchange with translation agencies.
- [Tests](tests): This app contains all tests to verify integreat-cms works as intended

To better understand the overall intention it might also be helpful to look at the [wiki for municipalities (GER)](https://wiki.integreat-app.de/) that teaches how to use our CMS.


## License

This project is licensed under the Apache 2.0 License, see [LICENSE.txt](./LICENSE.txt)

All files in [./integreat_cms/static/src/logos/](./integreat_cms/static/src/logos/) are not covered by this license and may only be used with specific permission of the copyright holder.
