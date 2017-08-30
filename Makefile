
clean:
	rm -rf flask_application/build


dependencies:


lambda:
	mkdir -p lambda
	cp -r flask_application lambda/
	rm -rf lambda/flask_application/static/images
	rm -rf lambda/flask_application/build
	cp update.py lambda/
	cp requirements.txt lambda/
	cd lambda && STATIC_DEPS=true pip install -U retrying facebook-sdk twitter pytz -t .
	zip -r lambda_bundle lambda/*
	# make clean


build: flask_application/build

flask_application/build:
	python frozen.py

test:
	py.test --verbose   --full-trace

s3_upload: build
	s3cmd sync --acl-public --delete-removed flask_application/build/ s3://reformedconfessions.com/


.PHONY: s3_upload clean build lambda