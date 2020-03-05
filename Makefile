SOURCES :=$(shell find content -name "*.md" | xargs echo | sed 's/\.md/\.html/g' | sed 's/\content/\build/g' )

all: ${SOURCES}
	echo "Sources" ${SOURCES}

%.html:
	./build_page.sh "$@"

