#!/bin/bash
set +x
set +e
input=${1/build\/westminster-daily/content}
input=${input%.html}.md
mkdir -p "$(dirname $1)"
pandoc --from markdown+footnotes --template templates/base.html --to html -o "$1" "$input"
