#!/bin/bash

# This script can be used to re-generate the translation file and compile it. It is also executed in run.sh

# Activate venv
cd $(dirname "$BASH_SOURCE")/..
source .venv/bin/activate

# Change directory to make sure to ignore files in the venv
cd backend/cms

# Reset environment variable to make sure makemessages works
export DJANGO_SETTINGS_MODULE=

# Re-generating translation file
integreat-cms makemessages -l de

# Ignore POT-Creation-Date of otherwise unchanged translation file
if git diff --shortstat locale/de/LC_MESSAGES/django.po | grep -q "1 file changed, 1 insertion(+), 1 deletion(-)"; then
    # Check if script was called with sudo (e.g. from run.sh for docker) and make sure git checkout is not called as root (would change the file permissions)
    if [ -z "$SUDO_USER" ]; then
        git checkout -- locale/de/LC_MESSAGES/django.po
    else
        # Execute command as user who executed sudo (inbuilt environment variable)
        su -c "git checkout -- locale/de/LC_MESSAGES/django.po" $SUDO_USER
    fi
fi

# Compile translation file
integreat-cms compilemessages
