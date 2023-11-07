#!/bin/bash

# This script checks if all dependencies in the lock files are up to date and increments the version numbers if necessary.

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Format a line according to pyproject.toml including indentation, quotes and comma
# E.g. "Django==4.1.7" is converted to "    "\Django==4.1.7\","
function format_pyproject_toml {
    while IFS= read -r line; do
        echo "${line}" | sed --regexp-extended 's/^(.*)$/    "\1",\\n/g' | tr -d '\n'
    done
}

require_installed
ensure_not_root

# Parse command line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    --python) PYTHON="$2"; shift 2;;
    --python=*) PYTHON="${1#*=}"; shift 1;;
    *) echo "Unknown option: $1" | print_error; exit 1;;
  esac
done

if [[ -n "${PYTHON}" ]]; then
    PYTHON=$(command -v "${PYTHON}")
    if [[ ! -x "${PYTHON}" ]]; then
        echo "The given python command '${PYTHON}' is not executable." | print_error
        exit 1
    fi
else
    # Default python binary
    PYTHON="python3"
fi

# Check if npm dependencies are up to date
echo "Updating JavaScript dependencies..." | print_info
npm update

# Fix npm security issues (skip all breaking changes)
echo "Running security audit of JavaScript dependencies..." | print_info
npm audit fix || true

# Update pip dependencies
echo "Updating Python dependencies..." | print_info
# Create temporary venv to make sure dev dependencies are not included initially
${PYTHON} -m venv .venv.tmp
source .venv.tmp/bin/activate
# Install package locally (without the pinned extra, so the newest available versions are installed)
pip install -e .
# Parse the newly installed versions
PINNED_VERSIONS=$(pip freeze --exclude-editable --local | sort)
PINNED_VERSIONS_TOML=$(echo "${PINNED_VERSIONS}" | format_pyproject_toml)
# Now also install dev dependencies
pip install -e .[dev]
# Parse the newly installed versions
PINNED_VERSIONS_ALL=$(pip freeze --exclude-editable --local | sort)
# Only consider packages that were not already pinned in the normal dependencies
PINNED_DEV_VERSIONS=$(comm -3 <(echo "${PINNED_VERSIONS_ALL}") <(echo "${PINNED_VERSIONS}"))
PINNED_DEV_VERSIONS_TOML=$(echo "${PINNED_DEV_VERSIONS}" | format_pyproject_toml)
# Write the new versions to pyproject.toml
sed --in-place --regexp-extended \
    --expression "/^pinned = \[$/,/^\]$/c\pinned = [\n${PINNED_VERSIONS_TOML}]" \
    --expression "/^dev-pinned = \[$/,/^\]$/c\dev-pinned = [\n${PINNED_DEV_VERSIONS_TOML}]" \
    pyproject.toml
# Remove the temporary venv
deactivate
rm -rf .venv.tmp

# Install updated versions in the real venv
if [[ -d ".venv" ]]; then
    # shellcheck disable=SC2102
    pip install -e .[dev-pinned,pinned]
else
    bash "${DEV_TOOL_DIR}/install.sh"
fi

echo "✔ Updated pyproject.toml and installed the new versions" | print_success
