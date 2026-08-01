#!/bin/bash
# Build a reference page (one catechism question or confession chapter)
# from markdown to HTML.
#
# Usage: ./build_reference_page.sh build/westminster-shorter-catechism/1/index.html

set -e

input="${1#build/}"
input="content-reference/${input%/index.html}/index.md"

mkdir -p "$(dirname "$1")"
pandoc --from markdown+footnotes --template templates/base.html --to html \
    --wrap=preserve -o "$1" "$input"
