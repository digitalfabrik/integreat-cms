#!/bin/bash

# This script can be used to check the translation file for missing or empty entries.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# Change directory to make sure to ignore files in the venv
cd "${BASE_DIR}/src/cms"

# Relative path from src/cms
TRANSLATION_FILE="locale/de/LC_MESSAGES/django.po"

# Re-generating translation file
pipenv run integreat-cms-cli makemessages -l de > /dev/null

# Check if translation file is up to date
TRANSLATION_DIFF=$(git diff --shortstat $TRANSLATION_FILE)
# The translation file is up to date if the diff is either empty (which means the last change was less than a minute ago)
# or has exactly one changed line (which means only the timestamp changed)
[[ -z "$TRANSLATION_DIFF" ]] || echo "$TRANSLATION_DIFF" | grep -q "1 file changed, 1 insertion(+), 1 deletion(-)" && UP_TO_DATE=$? || UP_TO_DATE=$?

if [ $UP_TO_DATE -eq 0 ]; then
    # Reset the translation file if only the POT-Creation-Date changed
    git checkout -- $TRANSLATION_FILE
fi

# Check for empty entries
pcregrep -Mq 'msgstr ""\n\n' $TRANSLATION_FILE && EMPTY_ENTRIES=$? || EMPTY_ENTRIES=$?

# Check for fuzzy headers (automatic translation proposals)
grep -q "#, fuzzy" $TRANSLATION_FILE && FUZZY_ENTRIES=$? || FUZZY_ENTRIES=$?

# Check if there are any problems
if [ $UP_TO_DATE -ne 0 ] || [ $EMPTY_ENTRIES -eq 0 ] || [ $FUZZY_ENTRIES -eq 0 ]; then
    # Check for missing entries
    if [ $UP_TO_DATE -ne 0 ]; then
        echo -e "❌ Your translation file is not up to date! 💣" | print_error
        # Check if script is running in CircleCI context
        if [[ -z "$CIRCLECI" ]]; then
            echo -e "Please add the current changes to your commit:\n" | print_error
        else
            echo -e "Please run ./dev-tools/translate.sh and add the add the resulting changes to your commit:\n" | print_error
        fi
        git --no-pager diff --color $TRANSLATION_FILE | print_with_borders
    fi
    # Check for empty entries
    if [ $EMPTY_ENTRIES -eq 0 ]; then
        echo -e "❌ You have empty entries in your translation file. Please translate them manually:\n" | print_error
        echo -e "src/cms/$TRANSLATION_FILE"
        pcregrep -M -B2 -n --color=never 'msgstr ""\n\n' $TRANSLATION_FILE | sed '4~5d' | format_grep_output | print_with_borders
    fi
    # Check for fuzzy headers (automatic translation proposals)
    if [ $FUZZY_ENTRIES -eq 0 ]; then
        echo -e "❌ You have fuzzy headers in your translation file (See [1] for more information)." | print_error
        echo -e "Please review them manually, adjust the translation if necessary and remove the fuzzy header afterwards.\n" | print_error
        echo -e "src/cms/$TRANSLATION_FILE"
        grep -A3 -B1 -n --color=never "#, fuzzy" $TRANSLATION_FILE | format_grep_output | print_with_borders
        echo -e "[1]: https://www.gnu.org/software/gettext/manual/html_node/Fuzzy-Entries.html\n\n" >&2
    fi

    # Check if script is running in pre-commit context
    if [[ -n "$PRE_COMMIT" ]]; then
        echo -e "If you want to disable all pre-commit hooks for this commit, use:\n" | print_info
        echo -e "\tgit commit --no-verify\n" | print_bold
        echo -e "\nIf you only want to disable the translations hook for this commit, use:\n" | print_info
        echo -e "\tSKIP=translations git commit" | print_bold
        echo -e "\nIf you want to disable all pre-commit hooks for this repository entirely, use:\n" | print_info
        echo -e "\tpipenv run pre-commit uninstall" | print_bold
    fi
    exit 1
fi

echo "✔ Your translation file looks good!" | print_success
