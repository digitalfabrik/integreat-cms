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
TRANSLATION_FILE=src/cms/locale/de/LC_MESSAGES/django.mo
if [[ -f "${TRANSLATION_FILE}" ]]; then
    mv "${TRANSLATION_FILE}" "${TRANSLATION_FILE}.lock"
fi

# Remove all old rst and html files (in case source files have been deleted)
find sphinx -type f \( -name "*.rst" ! -name "index.rst" \) -delete
if [[ -d docs ]]; then
    rm -r docs
fi

# Generate new .rst files from source code
export SPHINX_APIDOC_OPTIONS="members,show-inheritance"
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
pipenv run sphinx-build -j auto sphinx docs

# Move german translation file to original file again
if [[ -f "${TRANSLATION_FILE}.lock" ]]; then
    mv "${TRANSLATION_FILE}.lock" "${TRANSLATION_FILE}"
fi

# Remove temporary intermediate build files
rm -r docs/.doctrees
rm -r docs/_sources
rm docs/.buildinfo
