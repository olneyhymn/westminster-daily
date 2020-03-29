SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
CURRENT_FILE := $(shell date -u +"content/%m/%d.md")

all: build ${SOURCES} build/index.html build/westminster-daily/index.html feed.xml

feed.xml: build
	tox -e feed
	mv feed.xml build/westminster-daily/

build: build/westminster-daily build/css/main.css
	cp -r static/* build
	find build
	rm -rf build/scss

build/westminster-daily:
	mkdir -p build/westminster-daily

build/css/main.css: static/scss/main.scss
	mkdir -p build/css/
	sass static/scss/main.scss build/css/main.css

build/index.html: build/westminster-daily/index.html
	cp build/westminster-daily/index.html build/index.html

build/westminster-daily/index.html: build/westminster-daily
	cp $(CURRENT_FILE) content/index.md
	./build_page.sh build/westminster-daily/index.html

%.html:
	./build_page.sh "$@"

FORCE:
