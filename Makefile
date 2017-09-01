
clean: clean_lambda
	rm -rf flask_application/build

clean_lambda:
	rm -f lambda_bundle.zip
	rm -rf lambda

update_lambda_functions: clean update_tweet update_facebook update_daily

update_tweet: lambda_bundle
	aws lambda update-function-code --function-name westminster-daily-tweet --zip-file fileb://lambda_bundle.zip

update_facebook: lambda_bundle
	aws lambda update-function-code --function-name westminster-daily-facebook --zip-file fileb://lambda_bundle.zip

update_daily: lambda_bundle
	aws lambda update-function-code --function-name Update-Westminster-Daily --zip-file fileb://lambda_bundle.zip
	aws lambda invoke --function Update-Westminster-Daily  --payload \{\} --invocation-type RequestResponse --region us-east-1 /tmp/ooutput

lambda_bundle: lambda lambda_bundle.zip

lambda_bundle.zip:
	cd lambda && zip -r ../lambda_bundle *

lambda:
	mkdir -p lambda
	cp -r flask_application lambda/
	rm -rf lambda/flask_application/static/images
	rm -rf lambda/flask_application/build
	cp update.py lambda/
	cp requirements.txt lambda/
	cd lambda && STATIC_DEPS=true pip3 install -U retrying facebook-sdk werkzeug twitter pytz -t .

build: flask_application/build

flask_application/build:
	python frozen.py

test:
	py.test --verbose   --full-trace

s3_upload: build
	s3cmd sync --acl-public --delete-removed flask_application/build/ s3://reformedconfessions.com/


.PHONY: s3_upload clean clean_lambda build lambda_bundle update_daily update_facebook update_tweet update_lambda_functions