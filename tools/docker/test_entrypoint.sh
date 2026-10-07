#!/bin/bash

# Entrypoint for the dockerized test runner (see docker-compose.test.yml).
#
# It prepares a CI-equivalent environment inside the container and then execs
# pytest, forwarding every argument it receives. The arguments are assembled by
# tools/test.sh on the host (verbosity, markers, coverage, selected tests, …),
# so the in-container run behaves exactly like the host run — only the
# environment (Python, OS, fonts, PostgreSQL version) is pinned to match CI.

set -eo pipefail

# Virtualenv lives on a named volume (see docker-compose.test.yml) so that
# dependencies are installed once and reused across runs. The container runs as
# the invoking host user; the image opens /home/circleci for traversal and
# pre-creates this mountpoint world-writable so that uid can reach and populate
# the volume regardless of its value (see tools/docker/Dockerfile.test).
UV_PROJECT_ENVIRONMENT="/home/circleci/venv"
export UV_PROJECT_ENVIRONMENT
if [[ ! -w "${UV_PROJECT_ENVIRONMENT}" ]]; then
    echo "The virtualenv volume at ${UV_PROJECT_ENVIRONMENT} is not writable by uid $(id -u)." >&2
    echo "This usually means the test image predates the permission fix; rebuild" >&2
    echo "it and reset the cached volume:" >&2
    echo "    docker compose --env-file /dev/null -f docker-compose.test.yml build" >&2
    echo "    docker compose --env-file /dev/null -f docker-compose.test.yml down --volumes" >&2
    exit 1
fi

# Recreate the venv when its interpreter is missing or no longer runnable. The
# base image tracks a floating cimg/python:3.13 tag, so a rebuild can bump the
# pyenv patch version (e.g. 3.13.11 -> 3.13.15) and leave the cached venv's
# bin/python symlink dangling. `python -m venv` without --clear keeps existing
# symlinks, so it would not repair such a venv; --clear rebuilds it from the
# current interpreter.
if [[ ! -x "${UV_PROJECT_ENVIRONMENT}/bin/python" ]] || ! "${UV_PROJECT_ENVIRONMENT}/bin/python" -c '' 2> /dev/null; then
    # Install the project with the exact locked versions CI uses. uv creates the
    # virtualenv on the volume if it does not exist yet, and the install is a
    # no-op on warm runs.
    echo "Installing dependencies (locked, matching CI)..."
    uv sync --locked
fi

# The .mo translation files are not committed; compile them so translation-
# dependent tests (e.g. the CSV feedback export) behave deterministically.
# Run from inside the package directory (like the CI compile-translations job):
# compilemessages walks every locale/ dir below the cwd, and the project root
# may contain a bind-mounted host virtualenv whose third-party .po files
# (e.g. sphinx) fail msgfmt with fatal errors.
echo "Compiling translations..."
(cd integreat_cms && uv run integreat-cms-cli compilemessages)

# Wait for the PostgreSQL service to accept connections. `depends_on` with a
# health check already gates startup, but this makes the dependency explicit and
# survives a restarted db container.
echo "Waiting for database at ${INTEGREAT_CMS_DB_HOST}:${INTEGREAT_CMS_DB_PORT}..."
uv run python - <<'PY'
import os
import socket
import sys
import time

host = os.environ.get("INTEGREAT_CMS_DB_HOST", "db")
port = int(os.environ.get("INTEGREAT_CMS_DB_PORT", "5432"))
for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            sys.exit(0)
    except OSError:
        time.sleep(1)
sys.exit(f"Database at {host}:{port} did not become reachable in time")
PY

echo "Running tests..."
exec uv run pytest "$@"
