#!/bin/bash

# This script can be used to run both our code style tools black and pylint.

cd $(dirname "$BASH_SOURCE")/..

# Run black
pipenv run black .

# Run pylint
pipenv run pylint_runner
