#!/bin/sh

script_dir=$(dirname "$BASH_SOURCE")

rm -rfv $script_dir/../.postgres
rm -rfv $script_dir/../backend/cms/migrations
