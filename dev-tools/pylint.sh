#!/bin/bash

# This script can be used to run the pylint_runner while ignoring migrations.

cd $(dirname "$BASH_SOURCE")/../src

# Activate venv
source ../.venv/bin/activate

# Run pylint
pylint_runner
