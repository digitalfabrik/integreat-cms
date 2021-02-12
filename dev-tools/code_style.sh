#!/bin/bash

# This script can be used to run both our code style tools black and pylint.

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

cd $(dirname "$BASH_SOURCE")/..

# Run black
pipenv run black .

# Run pylint
pipenv run pylint_runner
