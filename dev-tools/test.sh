#!/bin/bash

# TODO: make it possible to use without docker database

cd $(dirname "$BASH_SOURCE")/..

pipenv run integreat-cms-cli test cms --settings=backend.docker_settings
