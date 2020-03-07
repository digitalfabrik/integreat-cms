#!/bin/bash

# TODO: make it possible to use without docker database

source .venv/bin/activate

export DJANGO_SETTINGS_MODULE=backend.docker_settings

integreat-cms test cms