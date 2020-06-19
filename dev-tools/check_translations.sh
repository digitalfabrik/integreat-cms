#!/bin/bash

# This script can be used to check the translation file for missing or empty entries.

# Check if pcregrep is installed
if [ ! -x "$(command -v pcregrep)" ]; then
    echo "PCRE grep is not installed. Please install pcregrep manually and run this script again." >&2
    exit 1
fi

# Change directory to make sure to ignore files in the venv
cd $(dirname "$BASH_SOURCE")/../src/cms

# Re-generating translation file
pipenv run integreat-cms-cli makemessages -l de > /dev/null

# Check for missing entries
if ! git diff --shortstat locale/de/LC_MESSAGES/django.po | grep -q "1 file changed, 1 insertion(+), 1 deletion(-)"; then
    echo "Your translation file is not up to date. Please run ./dev-tools/translate.sh and check if any strings need manual translation." >&2
    exit 1
fi

# Check for empty entries
if pcregrep -Mq 'msgstr ""\n\n' locale/de/LC_MESSAGES/django.po; then
    echo "You have empty entries in your translation file. Please translate them manually." >&2
    exit 1
fi

# Check for fuzzy headers (automatic translation proposals)
if grep -q "#, fuzzy" locale/de/LC_MESSAGES/django.po; then
    echo -e "You have fuzzy headers in your translation file (See [1] for more information). Please review them manually, adjust the translation if necessary and remove the fuzzy header afterwards.\n\n[1]: https://www.gnu.org/software/gettext/manual/html_node/Fuzzy-Entries.html" >&2
    exit 1
fi

echo "Your translation file looks good!"
