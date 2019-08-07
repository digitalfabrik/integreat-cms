#!/bin/bash

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate
integreat-cms createsuperuser --username root --email ''
