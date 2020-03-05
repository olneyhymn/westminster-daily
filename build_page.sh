#!/bin/bash
set +x
input=${1/build/content}
input=${input%.html}.md
mkdir -p "$(dirname $1)"
pandoc --from markdown+footnotes --template templates/base.html --to html -o "$1" "$input"
