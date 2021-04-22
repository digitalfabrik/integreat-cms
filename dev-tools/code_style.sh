#!/bin/bash

# This script can be used to run both our code style tools black and pylint.

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

cd $(dirname "$BASH_SOURCE")/..

# Run black
pipenv --python 3.7 run black .

# Run pylint
pipenv --python 3.7 run pylint_runner
