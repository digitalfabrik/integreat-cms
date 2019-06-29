#!/bin/bash

# This script installs the CMS in a local virtual environment without
# the need for docker or any other virtualization technology. A Postgres
# SQL server is needed to run the CMS.
python3 -m venv .venv
source .venv/bin/activate
python3 setup.py develop
source .venv/bin/activate