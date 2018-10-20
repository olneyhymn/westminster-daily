update_lambda_functions:
	tox -e lambda

	aws lambda update-function-code --function-name westminster-daily-tweet --zip-file fileb://lambda_bundle.zip
	aws lambda update-function-code --function-name westminster-daily-facebook --zip-file fileb://lambda_bundle.zip

	aws lambda update-function-code --function-name Update-Westminster-Daily --zip-file fileb://lambda_bundle.zip
	aws lambda invoke --function Update-Westminster-Daily  --payload \{\} --invocation-type RequestResponse --region us-east-1 /tmp/ooutput

s3_upload:
	tox -e build
	s3cmd sync --acl-public --delete-removed flask_application/build/ s3://reformedconfessions.com/
	aws --profile=pythonplot.com  cloudfront create-invalidation --distribution-id E2EQLK7CSPOT0E --paths="/*"

.PHONY: s3_upload clean clean_lambda build lambda_bundle update_daily update_facebook update_tweet update_lambda_functions dig 