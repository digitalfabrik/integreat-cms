#!/bin/bash

# This script can be used to resolve git merge/rebase conflicts of the translation file

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
ensure_not_root

# Relative path to translation file from the base directory
TRANSLATION_FILE="integreat_cms/locale/de/LC_MESSAGES/django.po"

echo "Resolving translation conflicts..." | print_info

# Remove git conflict markers
sed --in-place --regexp-extended -e '/^<<<<<<< .+$/d' -e '/^=======$/d' -e '/^>>>>>>> .+$/d' "$TRANSLATION_FILE"

# Remove duplicated translations and show error if this is not possible
if ! msguniq --output-file "$TRANSLATION_FILE" "$TRANSLATION_FILE" 2>&1 \
  | sed --regexp-extended -e "s|^(${TRANSLATION_FILE}):([0-9]+):[0-9]+?:? (.+)$|\1 \x1b[1m(line \2) \x1b[1;31m\3\x1b[0;39m|g" -e "$ d"; then
    echo -e "\n❌ Not all conflicts could be solved automatically" | print_error
    echo "Please fix the mentioned problem(s) manually and run this script again." | print_bold
    exit 1
fi

# Check if conflicts remain
if grep --quiet "#-#-#-#-#" "$TRANSLATION_FILE"; then
    echo -e "\n$TRANSLATION_FILE"
    grep --before-context=2 --after-context=1 --line-number "#-#-#-#-#" "$TRANSLATION_FILE" | format_grep_output | print_with_borders
    echo -e "❌ Not all conflicts could be solved automatically" | print_error
    echo "Please resolve remaining conflicts (marked with \"#-#-#-#-#\") manually and run this script again." | print_bold
    exit 1
fi

echo "✔ All conflicts were successfully resolved" | print_success

# Check if status is "unmerged"
if git status --short "$TRANSLATION_FILE" | grep --quiet "UU ${TRANSLATION_FILE}"; then
    # Mark conflict as resolved by adding to the staging area
    git add "$TRANSLATION_FILE"
    GIT_ADD_TO_STAGING_AREA=1
fi

# Fix line numbers and empty lines
bash "${DEV_TOOL_DIR}/translate.sh"

if [[ -n "$GIT_ADD_TO_STAGING_AREA" ]]; then
    # If conflict was marked as resolved before, also stage the changed line numbers and removed newlines etc...
    git add "$TRANSLATION_FILE"
fi
