#!/bin/bash

# This script can be used to check whether the changelog file is in the correct format.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Relative path from base directory
CHANGELOG_FILE="CHANGELOG.md"

# Get the changelog with newlines converted to \n
CHANGELOG=$(awk -v ORS='\\n' '1' ${CHANGELOG_FILE})

# How the unreleased header should look like
UNRELEASED="UNRELEASED\n----------\n\n"

# Check whether the changelog starts with the correct header
if [[ "${CHANGELOG}" != "${UNRELEASED}"* ]]; then
    echo -e "The changelog needs to begin with the following lines:" | print_error
    echo -e "${BASE_DIR}/${CHANGELOG_FILE}"
    echo -e "${UNRELEASED}" | print_with_borders
    echo -e "(Exactly one newline required between the headline and the first changelog entry)"
    exit 1
fi

# Get latest release version
VERSION_NUM=$(pipenv run python -c "import integreat_cms; print(integreat_cms.__version__)")

# How the according headline should look like
UNDERLINE=$(echo "${VERSION_NUM}" | tr "[:print:]" "-")
VERSION="${VERSION_NUM}\n${UNDERLINE}\n\n"

# Check whether the version heading can still be found to avoid misleading error messages
if [[ "${CHANGELOG}" != *"${VERSION}"* ]]; then
    echo -e "Cannot find the section of the last released version in the changelog." | print_error
    echo -e "${BASE_DIR}/${CHANGELOG_FILE}"
    echo -e "${VERSION}" | print_with_borders
    exit 1
# Check whether the unreleased section is empty
elif [[ "${CHANGELOG}" == "${UNRELEASED}\n${VERSION}"* ]]; then
    echo -e "The UNRELEASED section of the changelog is currently empty." | print_info
# Check whether exactly two new lines are before the next version headline
elif [[ "${CHANGELOG}" != *"\n\n\n${VERSION}"* ]]; then
    echo -e "Please leave exactly two new lines between the last unreleased changelog entry and the latest released version heading." | print_error
    echo -e "${BASE_DIR}/${CHANGELOG_FILE}"
    echo -e "${VERSION}" | print_with_borders
    exit 1
else
    # Get current unreleased section (split by 3 sequential new lines and print the first record except the first three lines)
    UNRELEASED_ITEMS=$(awk -v RS='\n\n\n' 'NR==1 {print $0}' "${CHANGELOG_FILE}" | tail -n +4)
    # Check whether each item matches the required format
    ITEM_PATTERN="^\* \[ \[\#([0-9]+)\]\(https\:\/\/github\.com\/digitalfabrik\/integreat-cms\/issues\/([0-9]+)\) \] .+$"
    while IFS= read -r ITEM; do
        # Check whether line is empty
        if [[ "${ITEM}" == "" ]]; then
            echo -e "Please leave exactly one new line between the UNRELEASED heading and the first unreleased changelog entry, exactly two new lines between the last entry and the heading of version ${VERSION_NUM}, and no empty lines between the entries itself." | print_error
            exit 1
        # Check whether line matches the given pattern
        elif [[ ! "${ITEM}" =~ $ITEM_PATTERN ]]; then
            echo -e "The following entry does not match the required format:\n" | print_error
            echo -e "${ITEM}\n"
            echo -e "Please change it according to the following format:\n" | print_warning
            echo -e "* [ [#\x1b[1;35m<id>\x1b[0;39m](https://github.com/digitalfabrik/integreat-cms/issues/\x1b[1;35m<id>\x1b[0;39m]) ] \x1b[1;36m<message>\x1b[0;39m]\n"
            echo -e "(Replace \x1b[1;35m<id>\x1b[1;39m with the id of the issue/PR on GitHub and \x1b[1;36m<message>\x1b[1;39m with the description in imperative mood: https://cbea.ms/git-commit/#imperative)" | print_bold
            exit 1
        # Check whether the issue ids match
        elif [[ "${BASH_REMATCH[1]}" != "${BASH_REMATCH[2]}" ]]; then
            echo -e "The following entry (#${BASH_REMATCH[1]}) links to a different issue (#${BASH_REMATCH[2]}):\n" | print_error
            echo -e "${ITEM}\n"
            exit 1
        elif [[ "${ITEM}" == *'"'* ]]; then
            echo -e "Please remove the double quotes from this entry:\n" | print_error
            echo -e "${ITEM}\n"
            exit 1
        fi
    done <<< "${UNRELEASED_ITEMS}"
    echo -e "These entries are currently unreleased:" | print_info
    UNRELEASED_ITEMS_RAW=$(echo "${UNRELEASED_ITEMS}" | sed --regexp-extended 's|\[#([0-9]+)\]\(https://github\.com/digitalfabrik/integreat-cms/issues/([0-9]+)\)|#\1|')
    echo "${UNRELEASED_ITEMS_RAW}" | print_with_borders
fi

echo "✔ The changelog file looks good!" | print_success
