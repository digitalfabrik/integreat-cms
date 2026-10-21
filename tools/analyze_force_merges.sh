#!/bin/bash

#Analyze force merges vs total merges for the integreat-cms repository.
# A "force merge" is a PR that was merged while CI checks were failing.

#Usage:
#    export GITHUB_TOKEN="ghp_..."   # needs repo read access
#    tools/analyze_force_merge.sh [--since 2025-10-01][--until 2026-01-13][--months 6] [--output csv] [--detail]

#Requires: requests (pip install requests)

#Combination of time arguments: since | until | months
#--since                         -> since = since; until = now
#--since & --until               -> since = since; until = until
#--since & --months              -> since = since; until = since + months
#--since & --until (& --months)  -> since = since; until = until
#--until                         -> invalid
#--months                        -> since = now - months; until = now
#--months & --until              -> since = until - months; until = until

# Import utility functions
# shellcheck source=./tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

require_installed

python3 "${BASE_DIR:?}/tools/_analyze_force_merges.py" "$@"
