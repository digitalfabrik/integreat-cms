#!/bin/bash

# This script fixes the dependencies in setup.cfg according to the Pipenv lock file.

# Import utility functions
# shellcheck source=./dev-tools/_functions.sh
source "$(dirname "${BASH_SOURCE[0]}")/_functions.sh"

echo "Extracting dependency versions..." | print_info
# Use pipenv to extract the exact dependency versions from the Pipfile.lock and remove all lines with start with a space, # or -
DEPENDENCY_VERSIONS=$(pipenv requirements | sed "/^[#-]/d")
echo "${DEPENDENCY_VERSIONS}"

# Use python to write the dependencies into the setup.cfg config file
python3 << EOF
import configparser
setup_cfg = configparser.ConfigParser(interpolation=None)
setup_cfg.read("${BASE_DIR}/setup.cfg")
setup_cfg["options"]["install_requires"] = """${DEPENDENCY_VERSIONS}"""
with open("${BASE_DIR}/setup.cfg", "w") as setup_cfg_file:
    setup_cfg.write(setup_cfg_file)
EOF
echo -e "✔ Fixed dependency versions in setup.cfg" | print_success
