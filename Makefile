SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
CURRENT_FILE := $(shell date -u +"content/%m/%d.md")
HEIDELBERG_SOURCES :=$(shell find content-heidelberg -name "*.md" 2>/dev/null | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content-heidelberg/build\/heidelberg-weekly/g' )

.PHONY: help
help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk -F ':|##' '/^[^\t].+?:.*?##/ { printf "  %-20s %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

all: build ${SOURCES} build/index.html build/westminster-daily/index.html feed.rss podcast.rss heidelberg-all redirects data-json ## Build entire site including HTML, RSS feeds and assets

heidelberg-all: build ${HEIDELBERG_SOURCES} build/heidelberg-weekly/index.html heidelberg-feed.rss ## Build Heidelberg Weekly site

feed.rss: build ## Generate main RSS feed
	uv run generate_feed.py
	mv feed.rss build/westminster-daily/

podcast.rss: build ## Generate podcast RSS feed
	uv run generate_podcast_feed.py
	mv podcast.rss build/westminster-daily/

build: og-images build/westminster-daily build/css/main.css ## Build site structure and compile CSS
	cp -r static/* build
	node scripts/generate-og-review.mjs --output build/og-review/index.html
	find build
	rm -rf build/scss

build/westminster-daily: ## Create Westminster Daily build directory
	mkdir -p build/westminster-daily

build/css/main.css: static/scss/main.scss package.json ## Compile SCSS to CSS
	mkdir -p build/css/
	npx sass --style=compressed --no-source-map static/scss/main.scss build/css/main.css

og-images: ## Generate Open Graph images
	node scripts/generate-og-images.mjs --all

og-image: ## Generate one Open Graph image (DATE=03/25 or WEEK=01)
	node scripts/generate-og-images.mjs $(if $(DATE),--date $(DATE),) $(if $(WEEK),--week $(WEEK),) $(if $(DEFAULT),--default,) $(if $(HEIDELBERG_DEFAULT),--heidelberg-default,)

build/index.html: build/westminster-daily/index.html ## Create root index.html
	cp build/westminster-daily/index.html build/index.html

build/westminster-daily/index.html: build/westminster-daily templates/base.html build_page.sh ## Generate Westminster Daily index page
	cp $(CURRENT_FILE) content/index.md
	./build_page.sh build/westminster-daily/index.html

build/westminster-daily/%.html: content/%.md templates/base.html build_page.sh ## Build individual HTML pages
	./build_page.sh "$@"

build/heidelberg-weekly/%/index.html: content-heidelberg/%/index.md templates/heidelberg-base.html build_heidelberg_page.sh ## Build Heidelberg Weekly pages
	./build_heidelberg_page.sh "$@"

build/heidelberg-weekly/index.html: build/heidelberg-weekly templates/heidelberg-base.html build_heidelberg_page.sh ## Generate Heidelberg Weekly index page
	python3 -c "from datetime import datetime, timedelta; \
		jan_1 = datetime(2024, 1, 1); \
		days_until_sunday = (6 - jan_1.weekday()) % 7; \
		first_sunday = jan_1 + timedelta(days=days_until_sunday if days_until_sunday > 0 or jan_1.weekday() != 6 else 0); \
		today = datetime.now(); \
		weeks_diff = (today - first_sunday).days // 7; \
		week_num = (weeks_diff % 52) + 1; \
		week_fmt = f'{week_num:02d}'; \
		import shutil; \
		shutil.copy(f'content-heidelberg/week-{week_fmt}/index.md', 'content-heidelberg/index.md')"
	./build_heidelberg_page.sh build/heidelberg-weekly/index.html

heidelberg-feed.rss: build ## Generate Heidelberg Weekly RSS feed
	uv run generate_heidelberg_feed.py
	mv heidelberg-feed.rss build/heidelberg-weekly/feed.rss

build/heidelberg-weekly: ## Create Heidelberg Weekly build directory
	mkdir -p build/heidelberg-weekly

redirects: build ## Generate _redirects file for Cloudflare Pages
	@echo "/static/audio/* https://s3.amazonaws.com/www.reformedconfessions.com/westminster-daily/static/audio/:splat 200" > build/_redirects
	@echo "/ /westminster-daily/ 200" >> build/_redirects
	@echo "/about /westminster-daily/about 200" >> build/_redirects

data-json: build/westminster-daily ## Copy data.json files into build
	find content -name "data.json" -exec sh -c 'dir=$$(dirname "{}"); dest="build/westminster-daily/$${dir#content/}"; mkdir -p "$$dest"; cp "{}" "$$dest/"' \;

FORCE:
