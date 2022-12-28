SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
CURRENT_FILE := $(shell date -u +"content/%m/%d.md")

all: build ${SOURCES} build/index.html build/westminster-daily/index.html feed.rss podcast.rss

feed.rss: build
	tox -e feed
	mv feed.rss build/westminster-daily/

podcast.rss: build
	tox -e podcastfeed
	mv podcast.rss build/westminster-daily/

build: build/westminster-daily build/css/main.css
	cp -r static/* build
	find build
	rm -rf build/scss

build/westminster-daily:
	mkdir -p build/westminster-daily

build/css/main.css: static/scss/main.scss
	mkdir -p build/css/
	node-sass --output-style compressed --source-map false static/scss/ -o build/css/

build/index.html: build/westminster-daily/index.html
	cp build/westminster-daily/index.html build/index.html

build/westminster-daily/index.html: build/westminster-daily
	cp $(CURRENT_FILE) content/index.md
	./build_page.sh build/westminster-daily/index.html

%.html:
	./build_page.sh "$@"

FORCE:
