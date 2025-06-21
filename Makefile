SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
CURRENT_FILE := $(shell date -u +"content/%m/%d.md")

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "  %-20s %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

all: build ${SOURCES} build/index.html build/westminster-daily/index.html feed.rss podcast.rss ## Build entire site including HTML, RSS feeds and assets

feed.rss: build ## Generate main RSS feed
	python -m pip install uv
	python -m uv run generate_feed.py
	mv feed.rss build/westminster-daily/

podcast.rss: build ## Generate podcast RSS feed
	python -m pip install uv
	python -m uv run generate_podcast_feed.py
	mv podcast.rss build/westminster-daily/

build: build/westminster-daily build/css/main.css ## Build site structure and compile CSS
	cp -r static/* build
	find build
	rm -rf build/scss

build/westminster-daily: ## Create Westminster Daily build directory
	mkdir -p build/westminster-daily

build/css/main.css: static/scss/main.scss ## Compile SCSS to CSS
	mkdir -p build/css/
	node-sass --output-style compressed --source-map false static/scss/ -o build/css/

build/index.html: build/westminster-daily/index.html ## Create root index.html
	cp build/westminster-daily/index.html build/index.html

build/westminster-daily/index.html: build/westminster-daily ## Generate Westminster Daily index page
	cp $(CURRENT_FILE) content/index.md
	./build_page.sh build/westminster-daily/index.html

%.html: ## Build individual HTML pages
	./build_page.sh "$@"

FORCE:
