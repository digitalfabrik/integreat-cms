#!/bin/bash

# This script installs the CMS in a local virtual environment without the need for docker or any other virtualization technology.
# A Postgres SQL server is needed to run the CMS (optionally inside a docker container).

cd $(dirname "$BASH_SOURCE")/..
python3 -m venv .venv
source .venv/bin/activate
pip3 install -e .[dev]
