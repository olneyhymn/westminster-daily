SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
REDIRECT := $(shell echo /     `date -u +"/%m/%d/"`)

all: ${SOURCES} /build/_redirects

%.html:
	./build_page.sh "$@"

/build/_redirects: FORCE
	echo $(REDIRECT)
	echo $(REDIRECT) > ./build/_redirects


FORCE:
