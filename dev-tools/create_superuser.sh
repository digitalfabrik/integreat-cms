#!/bin/bash

# This script creates a superuser for the cms with the username "root" and an empty email-field.
# It uses the settings for the postgres docker container and cannot be used with a standalone installation of postgres.

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate
export DJANGO_SETTINGS_MODULE=backend.docker_settings
integreat-cms createsuperuser --username root --email ''
