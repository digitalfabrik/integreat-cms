#!/bin/bash

cd $(dirname "$BASH_SOURCE")/../backend/cms/locale/de/LC_MESSAGES

# Replace git conflict markers
sed -i -E -e 's/<<<<<<< HEAD//g' django.po
sed -i -E -e 's/=======//g' django.po
sed -i -E -e 's/>>>>>>> .+//g' django.po

# Remove duplicated translations
msguniq -o django.po django.po

# Fix line numbers and empty lines
cd ../../../../../dev-tools
./translate.sh
