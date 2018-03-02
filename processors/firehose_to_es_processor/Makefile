ZIP_FILE := FirehoseCWLLogsProcessor_App.zip
TARGET := target/$(ZIP_FILE)
LAMBDA_CONFIG := ${PROJECT_ROOT}/config/iam-policy-templates/firehose-cwl-log-processor-lambda-deployment.json

.PHONY: build
build:
	rm -rf target
	mkdir target
	npm install
	zip -r $(TARGET) *.py

.PHONY: publish
publish:
	aws s3 rm s3://$(CODE_DEPLOYMENT_BUCKET)/$(ZIP_FILE)
	aws s3 cp $(TARGET) s3://$(CODE_DEPLOYMENT_BUCKET)/$(ZIP_FILE)

.PHONY: deploy
deploy:
	aws lambda update-function-code \
		--function-name $(shell cat $(LAMBDA_CONFIG) | jq -r '.FunctionName') \
		--s3-bucket $(shell cat $(LAMBDA_CONFIG) | jq -r '.Code.S3Bucket') \
		--s3-key $(shell cat $(LAMBDA_CONFIG) | jq -r '.Code.S3Key')
