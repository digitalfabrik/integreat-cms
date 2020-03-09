#!/bin/bash

# This script generates the documentation by scanning the source code and extracting definitions and doc strings.

# Check if script is running as root
if [ $(id -u) = 0 ]; then
    # Check if script was invoked by the root user or with sudo
    if [ -z "$SUDO_USER" ]; then
        echo "Please do not execute generate_documentation.sh as your root user because it would set the wrong file permissions of the documentation files." >&2
        exit 1
    else
        # Call this script again as the user who executed sudo
        sudo -u $SUDO_USER env PATH="$PATH" $0
        # Exit with code of subprocess
        exit $?
    fi
fi

cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate

# Move german translation file to prevent sphinx from translating strings
mv src/cms/locale/de/LC_MESSAGES/django.mo src/cms/locale/de/LC_MESSAGES/django.mo.lock

# Generate .rst files from source code
sphinx-apidoc --ext-autodoc --ext-coverage --force --no-toc --module-first -o sphinx src src/cms/migrations src/gvz_api/migrations

# Compile .rst files to html documentation
sphinx-build -E sphinx docs

# Move german translation file to original file again
mv src/cms/locale/de/LC_MESSAGES/django.mo.lock src/cms/locale/de/LC_MESSAGES/django.mo