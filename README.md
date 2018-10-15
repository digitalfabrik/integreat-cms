# Integreat CMS v2
## Local development setup
* `docker-compose up`
* enter [http://localhost:8000](http://localhost:8000)
* as long as there is no standard SQL dump, you have to create your own user: `docker exec -it cmsdjango_django_1 bash -c "python3 manage.py createsuperuser"`

## Production setup

## Miscellaneous
* keep in mind that we are using Python 3.x, so use `python3` and `pip3` on your bash commands
* get a bash shell in the django container: `docker exec -it cmsdjango_django_1 bash`

### Migrations
* change models
* `docker exec -it cmsdjango_django_1 bash -c "python3 manage.py makemigrations"`
* `docker exec -it cmsdjango_django_1 bash -c "python3 manage.py migrate"`

### pip dependencies
* freeze new installed dependencies via `docker exec -it cmsdjango_django_1 bash -c "pip3 freeze > requirements.txt"`
* install requirements via `docker exec -it cmsdjango_django_1 bash -c "pip3 install -r requirements.txt"`

### Docker clean up
* `docker stop $(docker ps -a -q)`
* `docker rm $(docker ps -a -q)`
* remove all images: `docker rmi $(docker images -a -q)`
* remove all volumes: `docker volume prune`