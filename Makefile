
clean:
	rm -rf flask_application/build

build: flask_application/build

flask_application/build:
	python frozen.py


s3_upload: build
	s3cmd sync --acl-public --delete-removed flask_application/build/ s3://reformedconfessions.com/


.PHONY: s3_upload clean build