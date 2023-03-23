#!/bin/bash

# This script can be used to generate the release notes

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Check if pcregrep is installed
if [[ ! -x "$(command -v pcregrep)" ]]; then
    echo "PCRE grep is not installed. Please install pcregrep manually and run this script again."  | print_error
    exit 1
fi

OUTPUT="/dev/stdout"
RELEASE_NOTES_DIR="integreat_cms/release_notes"

SUPPORTED_FORMATS=("md" "rst" "raw")
FORMAT="md"

SUPPORTED_LANGUAGES=("en" "de")
LANGUAGE="en"

# Parse command line arguments
while [ "$#" -gt 0 ]; do
  case "$1" in
    --format) FORMAT="$2"; shift 2;;
    --format=*) FORMAT="${1#*=}"; shift 1;;
    --language) LANGUAGE="$2"; shift 2;;
    --language=*) LANGUAGE="${1#*=}"; shift 1;;
    --output) OUTPUT="$2"; shift 2;;
    --output=*) OUTPUT="${1#*=}"; shift 1;;
    --version) ONLY_VERSION="$2"; shift 2;;
    --version=*) ONLY_VERSION="${1#*=}"; shift 1;;
    --all) ALL=1; shift 1;;
    --no-heading) NO_HEADING=1; shift 1;;
    --no-subheading) NO_SUBHEADING=1; shift 1;;
    *) echo "Unknown option: $1" | print_error; exit 1;;
  esac
done

# shellcheck disable=SC2076
if [[ ! " ${SUPPORTED_FORMATS[*]} " =~ " ${FORMAT} " ]]; then
    echo "The given format '${FORMAT}' is not supported (must be one of $(echo "${SUPPORTED_FORMATS[@]}" | tr ' ' ','))." | print_error
    exit 1
fi

# shellcheck disable=SC2076
if [[ ! " ${SUPPORTED_LANGUAGES[*]} " =~ " ${LANGUAGE} " ]]; then
    echo "The given language '${LANGUAGE}' is not supported (must be one of $(echo "${SUPPORTED_LANGUAGES[@]}" | tr ' ' ','))." | print_error
    exit 1
fi

if [[ -n ${ALL} ]]; then
    if [[ -n ${ONLY_VERSION} ]]; then
        echo "The option --version ${ONLY_VERSION} is incompatible with --all." | print_error
        exit 1
    fi
    if [[ -n ${NO_SUBHEADING} ]]; then
        echo "The option --no-subheading is incompatible with --all." | print_error
        exit 1
    fi
else
    if [[ -n ${ONLY_VERSION} ]]; then
        VERSION_TEXT=" for version ${ONLY_VERSION}"
    else
        VERSION_TEXT=" for the latest version"
    fi
fi
[[ "${OUTPUT}" != "/dev/stdout" ]] && echo "Building release notes${VERSION_TEXT}..." | print_info

function format_release_notes_entry {
    ISSUE=$(basename "$1" ".yml")
    TEXT=$(pcregrep --only-matching=1 "${LANGUAGE}: (.*)" "$1")
    if [[ ${FORMAT} == "md" ]]; then
        echo "- [ [#${ISSUE}](https://github.com/digitalfabrik/integreat-cms/issues/${ISSUE}) ] ${TEXT}"
    elif [[ ${FORMAT} == "rst" ]]; then
        echo "* [ :github-issue:\`${ISSUE}\` ] ${TEXT}"
    elif [[ ${FORMAT} == "raw" ]]; then
        echo "- [ #${ISSUE} ] ${TEXT}"
    fi
}

function format_release_notes_version {
    # Check if the --no-subheading option is given
    if [[ -z "${NO_SUBHEADING}" ]]; then
        VERSION=$(basename "$1")
        if [[ ${FORMAT} == "raw" ]]; then
            echo -e "${VERSION}\n"
        elif [[ ${FORMAT} == "md" ]]; then
            echo -e "## ${VERSION}\n"
        elif [[ ${FORMAT} == "rst" ]]; then
            if [[ ${VERSION} == "unreleased" ]]; then
                print_subheading "${VERSION}"
            else
                print_subheading ":github:\`${VERSION} <releases/tag/${VERSION}>\`"
            fi
        fi
    fi
    find "$1"/* -maxdepth 0 -type f | sort --version-sort | while read -r ENTRY; do
        format_release_notes_entry "${ENTRY}"
    done
    echo -e "\n"
}

function format_release_notes_year {
    find "$1"/* -maxdepth 0 -type d | sort --version-sort --reverse | while read -r VERSION; do
        format_release_notes_version "${VERSION}"
    done
}

# Make file empty
true > "${OUTPUT}"
# Check if the --include-heading option is given
if [[ -z "${NO_HEADING}" ]]; then
    if [[ ${FORMAT} == "md" ]]; then
        echo -e "# Release notes\n" >> "${OUTPUT}"
    elif [[ ${FORMAT} == "rst" ]]; then
        print_heading "Release notes" >> "${OUTPUT}"
    elif [[ ${FORMAT} == "raw" ]]; then
        echo -e "Release notes\n" >> "${OUTPUT}"
    fi
fi
if [[ -n ${ONLY_VERSION} ]]; then
    [[ ${ONLY_VERSION} == "unreleased" ]] && ONLY_VERSION_PATH="current" || ONLY_VERSION_PATH=$(echo "${ONLY_VERSION}" | cut -c1-4)
    if [[ ! -d "${RELEASE_NOTES_DIR}/${ONLY_VERSION_PATH}/${ONLY_VERSION}" ]]; then
        echo "The given version '${ONLY_VERSION}' does not exist." | print_error
        exit 1
    fi
    format_release_notes_version "${RELEASE_NOTES_DIR}/${ONLY_VERSION_PATH}/${ONLY_VERSION}" | sed '$ d' | sed '$ d' >> "${OUTPUT}"
elif [[ -n ${ALL} ]]; then
    # Append each year's entries
    find "${RELEASE_NOTES_DIR}"/* -maxdepth 0 -type d | sort --reverse | while read -r YEAR; do
        format_release_notes_year "${YEAR}" >> "${OUTPUT}"
    done
else
    # Only return the latest version by default
    format_release_notes_version "$(find "${RELEASE_NOTES_DIR}"/* -mindepth 1 -maxdepth 1 -type d | sort --version-sort | tail -n1)" | sed '$ d' | sed '$ d' >> "${OUTPUT}"
fi

if [[ "${OUTPUT}" != "/dev/stdout" ]]; then
    echo -e "✔ The release notes have been generated:\n" | print_success
    echo -e "\t${OUTPUT}\n" | print_bold
fi
