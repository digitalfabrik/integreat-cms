#!/bin/bash

# This script can be used to format the python code according to the black code style.

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

cd $(dirname "$BASH_SOURCE")/..

# Run black
pipenv --python 3.7 run black .

# Update translations (because changed formatting affects line numbers)
./translate.sh
