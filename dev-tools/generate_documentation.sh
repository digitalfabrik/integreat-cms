#!/bin/bash

# This script generates the documentation by scanning the source code and extracting definitions and doc strings.

# Configuration
SRC_DIR="src"
DOC_DIR="docs"
SPHINX_DIR="sphinx"
SPHINX_APIDOC_DIR="ref"
SPHINX_APIDOC_EXT_DIR="ref-ext"
TRANSLATION_FILE="src/cms/locale/de/LC_MESSAGES/django.mo"

if [[ "$VIRTUAL_ENV" != "" ]]
then
  export PIPENV_VERBOSITY=-1
fi

# Check if script is running as root
if [ $(id -u) = 0 ]; then
    # Check if script was invoked by the root user or with sudo
    if [ -z "${SUDO_USER}" ]; then
        echo "Please do not execute generate_documentation.sh as your root user because it would set the wrong file permissions of the documentation files." >&2
        exit 1
    else
        # Call this script again as the user who executed sudo
        sudo -u ${SUDO_USER} env PATH="${PATH}" $0
        # Exit with code of subprocess
        exit $?
    fi
fi

cd $(dirname "${BASH_SOURCE}")/..

# Copy original footer file
cp $(pipenv --venv)/lib/python3.7/site-packages/sphinx_rtd_theme/footer.html ${SPHINX_DIR}/templates
# Patch footer to add hyperlinks to copyright information
if ! patch ${SPHINX_DIR}/templates/footer.html ${SPHINX_DIR}/patches/footer.diff; then
    echo -e "\nThe patch for the footer template could not be applied correctly." >&2
    echo "Presumably the upstream repository of sphinx_rtd_theme changed." >&2
    echo "Please adapt ${SPHINX_DIR}/patches/footer.diff to the upstream changes." >&2
    exit 1
fi

# Copy original breadcrumbs file
cp $(pipenv --venv)/lib/python3.7/site-packages/sphinx_rtd_theme/breadcrumbs.html ${SPHINX_DIR}/templates
# Patch footer to add hyperlinks to copyright information
if ! patch ${SPHINX_DIR}/templates/breadcrumbs.html ${SPHINX_DIR}/patches/breadcrumbs.diff; then
    echo -e "\nThe patch for the breadcrumbs template could not be applied correctly." >&2
    echo "Presumably the upstream repository of sphinx_rtd_theme changed." >&2
    echo "Please adapt ${SPHINX_DIR}/patches/breadcrumbs.diff to the upstream changes." >&2
    exit 1
fi

# Generate new .rst files from source code for maximum verbosity
export SPHINX_APIDOC_OPTIONS="members,undoc-members,inherited-members,show-inheritance"
pipenv run sphinx-apidoc --no-toc --module-first -o ${SPHINX_DIR}/${SPHINX_APIDOC_EXT_DIR} ${SRC_DIR} ${SRC_DIR}/cms/migrations ${SRC_DIR}/gvz_api/migrations

# Modify .rst files to remove unnecessary submodule- & subpackage-titles
# Example: "cms.models.push_notifications.push_notification_translation module" becomes "Push Notification Translation"
# At first, the 'find'-command returns all .rst files in the sphinx directory
# The sed pattern replacement is divided into five stages explained below:
find ${SPHINX_DIR}/${SPHINX_APIDOC_EXT_DIR} -type f -name "*.rst" | xargs -r sed -i \
    -e '/Submodules\|Subpackages/{N;d;}' `# Remove Sub-Headings including their following lines` \
    -e 's/\( module\| package\)//' `# Remove module & package strings at the end of headings` \
    -e '/^[^ ]\+$/s/\(.*\.\)\?\([^\.]\+\)/\u\2/' `# Remove module path in headings (separated by dots) and make first letter uppercase` \
    -e '/^[^ ]\+$/s/\\_\([a-z]\)/ \u\1/g' `# Replace \_ with spaces in headings and make following letter uppercase` \
    -e 's/Cms/CMS/g;s/Api/API/g;s/Poi/POI/g;s/Mfa/MFA/g;s/Pdf/PDF/g' # Make specific keywords uppercase

# Remove inherited members from tests
find ${SPHINX_DIR}/${SPHINX_APIDOC_EXT_DIR} -type f -name "cms.tests*.rst" | xargs -r sed -i '/:inherited-members:/d'
# Include _urls in sitemap automodule
grep -rL ":private-members:" ${SPHINX_DIR}/*/sitemap.rst | xargs -r sed -i '/^\.\. automodule:: sitemap\.sitemaps/a \ \ \ :private-members:'

# Patch cms.rst to add the decorated functions
PATCH_STDOUT=$(patch --forward ${SPHINX_DIR}/${SPHINX_APIDOC_EXT_DIR}/cms.rst ${SPHINX_DIR}/patches/cms.diff)
# Check if the patch failed and a real error occurred (not only skipping because the patch is already applied)
if [[ $? -ne 0 ]] && ! echo "$PATCH_STDOUT" | grep -q "Reversed (or previously applied) patch detected!  Skipping patch."; then
    echo -e "\nThe patch for cms.rst could not be applied correctly." >&2
    echo "Presumably the structure of the cms package changed." >&2
    echo "Please adapt ${SPHINX_DIR}/patches/cms.diff to the structure changes." >&2
    exit 1
fi
echo "$PATCH_STDOUT"

# Generate new .rst files from source code for simple version (noindex to prevent double targets for the same source file)
cp -R ${SPHINX_DIR}/${SPHINX_APIDOC_EXT_DIR}/. ${SPHINX_DIR}/${SPHINX_APIDOC_DIR}

# Remove undocumented and inherited members from normal reference and set noindex
find ${SPHINX_DIR}/${SPHINX_APIDOC_DIR} -type f -name "*.rst" | xargs -r sed -i \
    -e '/:undoc-members:/d' `# Remove undoc-members from normal ref` \
    -e '/:inherited-members:/d' `# Remove inherited-members from normal ref` \
    -e '/:show-inheritance:/a \ \ \ :noindex:' # Insert :noindex: after :show-inheritance: option

# Add :noindex: to decorated functions in cms.rst inserted by the patch
sed -i '/\.\. autofunction:: /a \ \ \ \ \ \ :noindex:' ${SPHINX_DIR}/${SPHINX_APIDOC_DIR}/cms.rst

# Set verbose reference as orphans to suppress warnings about toctree
grep -rL ":orphan:" ${SPHINX_DIR}/${SPHINX_APIDOC_EXT_DIR}/*.rst | xargs -r sed -i '1s/^/:orphan:\n\n/'

# Compile .rst files to html documentation
pipenv run sphinx-build -j auto -W --keep-going ${SPHINX_DIR} ${DOC_DIR}

# Get exit status of sphinx-build
status=$?

# Check if script is running in CircleCI context
if [[ -n "$CIRCLECI" ]]; then
    # Remove temporary intermediate build files (they should not be committed to gh-pages)
    rm -r docs/.doctrees
    rm -r docs/_sources
    rm docs/.buildinfo
fi

# Exit with status of sphinx-build
exit $status
