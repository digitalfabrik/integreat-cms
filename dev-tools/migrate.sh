#!/bin/sh

source .venv/bin/activate
integreat-cms makemigrations cms
integreat-cms migrate
integreat-cms loaddata backend/cms/fixtures/roles.json