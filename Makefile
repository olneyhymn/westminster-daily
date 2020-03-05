SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
CURRENT_FILE := $(shell date -u +"content/%m/%d.md")

all: build ${SOURCES} build/index.html build/westminster-daily/index.html

build: build/westminster-daily

build/westminster-daily:
	mkdir -p build/westminster-daily

build/index.html: build/westminster-daily/index.html
	cp build/westminster-daily/index.html build/index.html

build/westminster-daily/index.html: build/westminster-daily
	cp $(CURRENT_FILE) content/index.md
	./build_page.sh build/westminster-daily/index.html

%.html:
	./build_page.sh "$@"

FORCE:
