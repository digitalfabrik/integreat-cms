#!/bin/bash

# This script creates a superuser for the cms with the username "root" and an empty email-field.
# It uses the settings for the postgres docker container and cannot be used with a standalone installation of postgres.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_database

deescalate_privileges pipenv run integreat-cms-cli createsuperuser
