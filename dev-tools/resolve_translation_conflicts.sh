#!/bin/bash

# This script can be used to resolve git merge/rebase conflicts of the translation file

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

ensure_not_root

cd "${BASE_DIR}/src/cms/locale/de/LC_MESSAGES" || exit 1

# Replace git conflict markers
sed -i -E -e 's/<<<<<<< HEAD//g' django.po
sed -i -E -e 's/=======//g' django.po
sed -i -E -e 's/>>>>>>> .+//g' django.po

# Remove duplicated translations
msguniq -o django.po django.po

# Check if conflicts remain
if grep -q "#-#-#-#-#" django.po; then
    echo "Not all conflicts could be solved automatically. Please resolve remaining conflicts manually (marked with \"#-#-#-#-#\")."
else
    # Fix line numbers and empty lines
    bash "${DEV_TOOL_DIR}/translate.sh"
fi
