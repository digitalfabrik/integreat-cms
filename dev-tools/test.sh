#!/bin/bash
if ! command -v jsdoc &> /dev/null
then
	export PATH="$PATH:$(realpath $PWD/../node_modules/.bin)"
fi
