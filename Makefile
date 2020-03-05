SOURCES :=$(shell find content -name "*.md" | tr '\n' ' ' | sed 's/\.md/\.html/g; s/content/build/g' )

all: ${SOURCES}
	echo "Sources" ${SOURCES}

%.html:
	./build_page.sh "$@"

