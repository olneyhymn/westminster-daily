#!/bin/bash
# Build a Heidelberg Weekly page from markdown to HTML
# Usage: ./build_heidelberg_page.sh build/heidelberg-weekly/week-01/index.html

input="${1#build/heidelberg-weekly/}"
if [ "$input" = "index.html" ]; then
    input="content-heidelberg/index.md"
else
    input="content-heidelberg/${input%/index.html}/index.md"
fi
mkdir -p "$(dirname "$1")"
pandoc --from markdown+footnotes --template templates/heidelberg-base.html --to html -o "$1" "$input"
