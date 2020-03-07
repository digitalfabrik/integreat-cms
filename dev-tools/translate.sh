#!/bin/bash

# This script can be used to re-generate the translation file and compile it. It is also executed in run.sh

# Check if script is running as root
if [ $(id -u) = 0 ]; then
    # Check if script was invoked by the root user or with sudo
    if [ -z "$SUDO_USER" ]; then
        echo "Please do not execute translate.sh as your root user because it would change the file permissions of your translation file." >&2
        exit 1
    else
        # Call this script again as the user who executed sudo
        sudo -u $SUDO_USER env PATH="$PATH" $0
        # Exit with code of subprocess
        exit $?
    fi
fi

# Activate venv
cd $(dirname "$BASH_SOURCE")
source ../.venv/bin/activate

# Change directory to make sure to ignore files in the venv
cd ../src/cms

# Re-generating translation file
integreat-cms-cli makemessages -l de

# Ignore POT-Creation-Date of otherwise unchanged translation file
if git diff --shortstat locale/de/LC_MESSAGES/django.po | grep -q "1 file changed, 1 insertion(+), 1 deletion(-)"; then
    git checkout -- locale/de/LC_MESSAGES/django.po
fi

# Compile translation file
integreat-cms-cli compilemessages
