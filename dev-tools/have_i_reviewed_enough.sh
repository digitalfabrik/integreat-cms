#!/bin/bash

# This script retrieves stats about the pull request reviews from GitHub

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

# Check if requirements are satisfied
if [[ ! -x "$(command -v gh)" ]]; then
    echo "The GitHub cli is not installed. Please install github-cli manually and run this script again."  | print_error
    exit 1
fi

# Parse command line arguments
while [ "$#" -gt 0 ]; do
    case "$1" in
        --since) SINCE="$2"; shift 2;;
        --since=*) SINCE="${1#*=}"; shift 1;;
        *) echo "Unknown option: $1" | print_error; exit 1;;
    esac
done

if [[ -n "${SINCE}" ]]; then
    PARSED_DATE=$(date --date="${SINCE}" --iso-8601)
    UPDATED_FLAG="--updated >=${PARSED_DATE}"
    SINCE_TEXT=" since ${PARSED_DATE}"
fi

# Configuration
REPOSITORY="digitalfabrik/integreat-cms"
BRANCH="develop"
LIMIT=1000

# Get the username via the prs search command to avoid requiring jq as direct dependency
# (gh api user | jq -r ".login") would be an alternative
# See https://stedolan.github.io/jq/manual/ for JQ documentation
JQ_GET_USERNAME=".[].author.login | if . == null then \"@me\" else . end"
USERNAME=$(gh search prs --author @me --limit 1 --json author --jq "${JQ_GET_USERNAME}")

echo "Retrieving GitHub stats for ${USERNAME}${SINCE_TEXT}..." | print_info

# The date when we switched from one required reviews per PR to two
TWO_REVIEWS_SINCE="2022-09-18"
# This returns two counters of all PRs openend before and after $TWO_REVIEWS_SINCE
# See https://stedolan.github.io/jq/manual/ for JQ documentation
JQ_SPLIT_BY_CREATION="reduce .[] as \$pr ([0,0]; if (\$pr | .createdAt) < \"${TWO_REVIEWS_SINCE}\" then .[0] += 1 else .[1] += 1 end) | .[]"
# shellcheck disable=SC2086,SC2207
OPENED=($(gh search prs \
    --repo "${REPOSITORY}" \
    --base "${BRANCH}" \
    --author "${USERNAME}" \
    --limit "${LIMIT}" \
    --json "createdAt" \
    --jq "${JQ_SPLIT_BY_CREATION}" \
    ${UPDATED_FLAG} \
))
OPENED_TOTAL=$((OPENED[0]+OPENED[1]))

# Do not count review comments on own PRs into the score
# See https://stedolan.github.io/jq/manual/ for JQ documentation
JQ_REMOVE_OWN="del(.[] | select(.author.login == \"${USERNAME}\")) | length"
# shellcheck disable=SC2086
REVIEWED_TOTAL=$(gh search prs \
    --repo "${REPOSITORY}" \
    --base "${BRANCH}" \
    --reviewed-by "${USERNAME}" \
    --limit "${LIMIT}" \
    --json "author" \
    --jq "${JQ_REMOVE_OWN}" \
    ${UPDATED_FLAG} \
)

# Require two reviews for every PR opened after $TWO_REVIEWS_SINCE (and one review for each PR before)
REVIEWED_GOAL=$((OPENED[0]+2*OPENED[1]))
REVIEW_SCORE=$((REVIEWED_TOTAL-REVIEWED_GOAL))

echo -e "You have worked on $(colorize_number "${OPENED_TOTAL}") own PRs and reviewed $(colorize_number "${REVIEWED_TOTAL}") (goal: \x1b[1m${REVIEWED_GOAL}\x1b[0m) other PRs.\n"
echo -e "\tCurrent reviewing score: $(colorize_number "${REVIEW_SCORE}" sign)\n"

if [[ "${REVIEW_SCORE}" -eq "0" ]]; then
    echo -e "👍 Awesome, you met your goal. Keep up the good work!" | print_info
elif [[ "${REVIEW_SCORE}" -ge "0" ]]; then
    echo -e "💪 Wow, you're unstoppable. Thanks a lot for your dedication!" | print_success
else
    echo -e "😼 Thanks for opening so many PRs, but please don't forget to review the PRs of others." | print_warning
fi
