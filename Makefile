
clean: clean_lambda clean_build clean_css

server: sass
	FLASK_APP=flask_application/app.py flask run

clean_build:
	rm -rf flask_application/build
	rm -rf flask_application/bower_components

clean_css:
	rm -rf flask_application/static/css

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

build: clean_build flask_application/bower_components sass flask_application/build

sass: flask_application/bower_components flask_application/static/css

flask_application/static/css:
	npm run css

flask_application/bower_components:
	cd flask_application && bower install bootstrap#v4.0.0-beta
	cd flask_application && bower install bigfoot


dig:
	dig CNAME reformedconfessions.com
	dig CNAME www.reformedconfessions.com

curl:
	curl -IL reformedconfessions.com
	curl -IL www.reformedconfessions.com

flask_application/build:
	python frozen.py

test:
	py.test --verbose   --full-trace

s3_upload: build
	s3cmd sync --acl-public --delete-removed flask_application/build/ s3://reformedconfessions.com/
	aws --profile=pythonplot.com  cloudfront create-invalidation --distribution-id E2EQLK7CSPOT0E --paths="/*"


.PHONY: s3_upload clean clean_lambda build lambda_bundle update_daily update_facebook update_tweet update_lambda_functions dig clean_build css server clean_css