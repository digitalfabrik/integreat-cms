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
# dependencies are installed once and reused across runs.
VENV_DIR="/home/circleci/venv"
# Named-volume mount points are created owned by root; make the venv directory
# writable by the unprivileged container user before using it (cimg images grant
# the `circleci` user passwordless sudo).
if [[ ! -w "${VENV_DIR}" ]]; then
    sudo chown "$(id -u):$(id -g)" "${VENV_DIR}"
fi
if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "Creating virtualenv at ${VENV_DIR}..."
    python -m venv "${VENV_DIR}"
    "${VENV_DIR}/bin/pip" install --upgrade pip
fi
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

# Install the project with the same pinned dependency sets CI uses. This is a
# no-op on warm runs (the venv volume is cached) and fast thanks to the pip
# cache volume.
echo "Installing dependencies (pinned, matching CI)..."
pip install -e ".[dev-pinned,pinned]"

# The .mo translation files are not committed; compile them so translation-
# dependent tests (e.g. the CSV feedback export) behave deterministically.
echo "Compiling translations..."
integreat-cms-cli compilemessages

# Wait for the PostgreSQL service to accept connections. `depends_on` with a
# health check already gates startup, but this makes the dependency explicit and
# survives a restarted db container.
echo "Waiting for database at ${INTEGREAT_CMS_DB_HOST}:${INTEGREAT_CMS_DB_PORT}..."
python - <<'PY'
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
exec pytest "$@"
