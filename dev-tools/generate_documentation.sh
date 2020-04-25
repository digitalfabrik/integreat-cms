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

# Move german translation file to prevent sphinx from translating strings
mv src/cms/locale/de/LC_MESSAGES/django.mo src/cms/locale/de/LC_MESSAGES/django.mo.lock

# Remove all old rst files (in case source files have been deleted)
find sphinx -type f \( -name "*.rst" ! -name "index.rst" \) -delete

# Generate new .rst files from source code
SPHINX_APIDOC_OPTIONS="members,show-inheritance"
pipenv run sphinx-apidoc --no-toc --module-first -o sphinx src src/cms/migrations src/gvz_api/migrations

# Modify .rst files to remove unnecessary submodule- & subpackage-titles
# Example: "cms.models.push_notifications.push_notification_translation module" becomes "Push Notification Translation"
# At first, the 'find'-command returns all .rst files in the sphinx directory
# The sed pattern replacement is divided into five stages explained below:
find sphinx -type f -name "*.rst" | xargs sed -i \
    -e '/Submodules\|Subpackages/{N;d;}' `# Remove Sub-Headings including their following lines` \
    -e 's/\( module\| package\)//' `# Remove module & package strings at the end of headings` \
    -e '/^[^ ]\+$/s/\(.*\.\)\?\([^\.]\+\)/\u\2/' `# Remove module path in headings (separated by dots) and make first letter uppercase` \
    -e '/^[^ ]\+$/s/\\_\([a-z]\)/ \u\1/g' `# Replace \_ with spaces in headings and make following letter uppercase` \
    -e 's/Cms/CMS/g;s/Api/API/g;s/Poi/POI/g;s/Mfa/MFA/g' # Make specific keywords uppercase

# Compile .rst files to html documentation
pipenv run sphinx-build -E sphinx docs

# Move german translation file to original file again
mv src/cms/locale/de/LC_MESSAGES/django.mo.lock src/cms/locale/de/LC_MESSAGES/django.mo
