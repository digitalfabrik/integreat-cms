#!/bin/bash

# This script can be used to create a new release note

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed
require_gh_cli_installed

ISSUE=$1
LANGUAGE=$2
TEXT=$3

if ! [[ "${ISSUE}" =~ ^[0-9]+$ ]]; then
    echo "The given issue '${ISSUE}' is not a number." | print_error
    exit 1
fi

if [[ "${LANGUAGE}" == "en" ]]; then
    TEXT_EN=$3
    SOURCE_LANG="EN"
    TARGET_LANG="DE"
elif [[ "${LANGUAGE}" == "de" ]]; then
    TEXT_DE=$3
    SOURCE_LANG="DE"
    TARGET_LANG="EN"
else
    echo "The given language '${LANGUAGE}' is not supported (must be one of 'en', 'de')." | print_error
    exit 1
fi

if [[ -z "${TEXT}" ]] || [[ "${TEXT}" == "-"* ]]; then
    echo "The third command line argument needs to contain the release note text." | print_error
    exit 1
fi

RELEASE_NOTES_DIR="integreat_cms/release_notes"
UNRELEASED_DIR="${RELEASE_NOTES_DIR}/current/unreleased"
OUTPUT="${UNRELEASED_DIR}/${ISSUE}.yml"

TITLE=$(gh issue view "${ISSUE}" --json title --jq ".title")

echo -e "Creating new release note for issue #${ISSUE} with title:\n" | print_info
echo -e "\t${TITLE}\n" | print_bold

DEEPL_AUTH_KEY=$(integreat-cms-cli shell -c 'from django.conf import settings; print(settings.DEEPL_AUTH_KEY or "")')

if [[ -n "${DEEPL_AUTH_KEY}" ]]; then
    # Check if key belongs to free or pro account
    [[ "${DEEPL_AUTH_KEY}" == *":fx" ]] && DEEPL_API='https://api-free.deepl.com' || DEEPL_API='https://api.deepl.com'
    TEXT_TRANSLATED=$(curl -s -X POST "${DEEPL_API}/v2/translate" \
        -H "Authorization: DeepL-Auth-Key ${DEEPL_AUTH_KEY}" \
        -d "source_lang=${SOURCE_LANG}" \
        -d "target_lang=${TARGET_LANG}" \
        -d "text=$(echo "${TEXT}" | jq -sRr @uri)" \
        | jq -r '.[][0]["text"]' \
    )
else
    echo -e "Set a DeepL auth key in the config file to enable automatic translation of release notes." | print_warning
fi

if [[ "${LANGUAGE}" == "en" ]]; then
    TEXT_EN=$TEXT
    TEXT_DE=$TEXT_TRANSLATED
elif [[ "${LANGUAGE}" == "de" ]]; then
    TEXT_EN=$TEXT_TRANSLATED
    TEXT_DE=$TEXT
fi

# Make sure directory exists
mkdir -p "${UNRELEASED_DIR}"

if [[ -f "${OUTPUT}" ]]; then
    echo -e "Warning: The release note ${OUTPUT} already exists." | print_warning
    if [[ "$4" == "--overwrite" ]]; then
        echo -e "The existing file will be overwritten." | print_bold
    else
        echo -e "Use the --overwrite flag to overwrite the existing file." | print_bold
        exit 1
    fi
fi

# Generate release note
echo -e "en: ${TEXT_EN}\nde: ${TEXT_DE}" > "${OUTPUT}"

echo -e "✔ The new release note has been generated:\n" | print_success
echo -e "${OUTPUT}" | print_bold
print_with_borders < "${OUTPUT}"
