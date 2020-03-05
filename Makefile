SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build\/westminster-daily/g' )
REDIRECT1 := $(shell echo /     `date -u +"/westminster-daily/%m/%d/"`)
REDIRECT2 := $(shell echo /westminster-daily/     `date -u +"/westminster-daily/%m/%d/"`)

all: ${SOURCES} /build/_redirects

%.html:
	./build_page.sh "$@"

/build/_redirects: FORCE
	rm -f ./build/_redirects
	touch ./build/_redirects
	echo $(REDIRECT1) >> ./build/_redirects
	echo $(REDIRECT2) >> ./build/_redirects


FORCE:
