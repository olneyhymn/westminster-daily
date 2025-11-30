#!/bin/bash
# Build a Heidelberg Weekly page from markdown to HTML
# Usage: ./build_heidelberg_page.sh build/heidelberg-weekly/week-01/index.html

input="${1/build\/heidelberg-weekly/content-heidelberg}"
input="${input/index.html/index.md}"
mkdir -p "$(dirname "$1")"
pandoc --from markdown+footnotes --template templates/heidelberg-base.html --to html -o "$1" "$input"
