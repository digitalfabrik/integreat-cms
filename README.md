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

### Packaging
Packaging for Debian can be done with setuptools. Install `python3-stdeb`, then run
```
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install stdeb
$ python3 setup.py --command-packages=stdeb.command bdist_deb
```
The .spec file for building RPMs can be found at https://build.opensuse.org/package/show/home:sven15/integreat-cms-django

#### Installing on Ubuntu
To install the CMS as a .deb file, the python3-django-widget-tweaks needs to be build first.
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