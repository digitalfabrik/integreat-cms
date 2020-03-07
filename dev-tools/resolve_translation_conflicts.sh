#!/bin/bash

cd $(dirname "$BASH_SOURCE")/../src/cms/locale/de/LC_MESSAGES

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
    cd ../../../../../dev-tools
    ./translate.sh
fi
