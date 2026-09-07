#!/usr/bin/env bash

project_home=$(dirname "$(readlink -f "$0"/..)")

uv run "${project_home}/cli.py" source ruff_format "$@"