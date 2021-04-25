#!/bin/bash

# This file contains utility functions which can be used in the dev-tools.

# This function prints the major version of a string in the format XX.YY.ZZ
function major {
    # Split by "." and take the first element for the major version
    echo "$1" | cut -d. -f1
}

# This function prints the minor version of a string in the format XX.YY.ZZ
function minor {
    # Split by "." and take the second element for the minor version
    echo "$1" | cut -d. -f2
}

# This function prints the given input lines in red color
function print_error {
    while read -r line; do
        echo -e "\e[1;31m$line\e[0;39m" >&2
    done
}

# This function prints the given input lines in green color
function print_success {
    while read -r line; do
        echo -e "\e[1;32m$line\e[0;39m"
    done
}

# This function prints the given input lines with a nice little border to separate it from the rest of the content.
# Pipe your content to this function.
function print_with_borders {
    echo "┌──────────────────────────────────────"
    while read -r line; do
        echo "│ $line"
    done
    echo -e "└──────────────────────────────────────\n"
}
