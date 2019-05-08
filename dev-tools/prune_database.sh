#!/bin/sh

script_dir=$(dirname "$BASH_SOURCE")

rm -rfv $script_dir/../_postgres
rm -rfv $script_dir/../backend/cms/migrations
