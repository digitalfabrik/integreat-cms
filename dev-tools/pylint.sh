#!/bin/bash

# This script can be used to run the pylint_runner while ignoring migrations.

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

cd $(dirname "$BASH_SOURCE")/..

# Run pylint
pipenv run pylint_runner
