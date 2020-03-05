SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )

all: ${SOURCES}

%.html:
	./build_page.sh "$@"

