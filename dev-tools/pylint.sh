#!/bin/bash

# This script can be used to run the pylint_runner while ignoring migrations.

cd $(dirname "$BASH_SOURCE")/../src

# Run pylint
pipenv run pylint_runner
