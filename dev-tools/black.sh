#!/bin/bash

# This script can be used to format the python code according to the black code style.

cd $(dirname "$BASH_SOURCE")/..

# Run black
pipenv run black .
