#!/bin/bash

# This script can be used to create a branch matching an issue.
# It fetches the info from GitHub and suggests a prefix and slug
# matching our branch naming conventions.

# shellcheck disable=SC2154

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

# ANSI color sequences
#RED=$'\e[1;31m'
GREEN=$'\e[1;32m'
YELLOW=$'\e[1;33m'
BLUE=$'\e[1;34m'
#PURPLE=$'\e[1;35m'
COLRESET=$'\e[0;39m'

BOLD=$'\e[1;1m'
BOLDRESET=$'\e[1;0m'


echo "Getting info from GitHub..." | print_info
source <(.venv/bin/python tools/github-info.py "$1" issue)

# Show general info
echo "  ${BOLD}#${number}  ${issueType}${BOLDRESET}"
echo "  ${headline}"
echo "  ${YELLOW}${labels}${COLRESET}"

function slugify {
    # Convert the characters of the given argument into ASCII
    # where international characters like umlauts are substituted by their
    # base letter (ASCII equivalent) if possible
    # Ä → A, ß → ss, ł → l etc.
    # (Doesn't turn Japanese into its romaji form, unfortunately,
    #  but luckily we tend to not have any issues opened in Japanese)
    transliterated=$(echo "$1" | iconv -f UTF-8 -t ASCII//TRANSLIT)

    # sed commands after ascii transliteration (does not contain äöüß anymore)
    sed_cmd=(
        's/\(.*\)/\L\1/'          # convert to lower case
        's/[^a-zA-Z0-9]\+/-/g'    # convert non-alphanumeric ranges to single hyphen
        's/^-//'                  # but discard leading hyphen
        's/-$//'                  # and discard trailing hyphen
    )
    # each regex filter needs to be supplied with -e individually
    sed_args=()
    for c in "${sed_cmd[@]}"; do
        sed_args+=(-e "$c")
    done

    # Return the slug
    echo "$transliterated" | sed "${sed_args[@]}"
}

prefix="chore"  # The default prefix if nothing else matches
[[ "$issueType" == "Bug" ]]     && prefix="fix"
[[ "$issueType" == "Feature" ]] && prefix="feat"

slug=$(slugify "$headline")


# Interactive block - give user chance to change input
if tty -s; then
    # Choose different prefix
    choices=(fix feat chore ai)
    # Show all choices, but with the pre-selected one shown in [brackets]
    choice_str=()
    for c in "${choices[@]}"; do
        if [[ "$c" == "$prefix" ]]; then
            # This choice is the currect pre-selected one, highlight it
            choice_str+=("[${GREEN}${c}${COLRESET}]")
        else
            # This is an alternative choice, just pad it with spaces
            # so they don't shift around when the pre-selected one changes
            choice_str+=(" $c ")
        fi
    done
    # Now prompt the user for their choice
    # This is a while loop that runs again and again until the choice is valid
    while true; do
        # Display prompt, save any characters sent before enter into $ans
        read -r -p "${BLUE}Set branch prefix (${COLRESET}${choice_str[*]}${BLUE}):${COLRESET} " ans

        # Some shell magic to match any choice in the $choices array
        # instead of listing them out individually
        IFS=@
        case "@${choices[*]}@" in
            (*"@$ans@"*)
                # $ans is in $choices, set it as the prefix
                prefix="$ans"
                break;;
            *)
                [[ "$ans" == "" ]] && break  # The user just pressed enter, keep default and move on
                # The user entered something else, ignore and prompt again
                ;;
        esac
    done


    # Give the option to adjust the branch name
    # Pre-fill it with $slug, save the result after pressing enter into $ans
    read -e -r -p "${BLUE}Set branch name:${COLRESET} ${prefix}/" -i "$slug" ans
    # Enforce a slugified result
    normalized=$(slugify "$ans")
    while [[ "$ans" != "$normalized" ]]; do
        # The slugified result differs from the raw result we got from the user,
        # meaning they didn't produce a valid one.
        # Prompt them again to make sure we capture their intention
        read -e -r -p "${YELLOW}Normalized slug:${COLRESET} ${prefix}/" -i "$normalized" ans
        normalized=$(slugify "$ans")
    done

    # The slugified result didn't change from what the user gave us, this is the new slug!
    slug="$ans"
fi


# Now we can assemble the branch name
branchName="${prefix}/${slug}"

git switch -c "$branchName"

echo "✔ Switched to $branchName" | print_success
