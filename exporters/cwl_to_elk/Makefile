ZIP_FILE := LogsToElasticsearch_App.zip
TARGET := target/$(ZIP_FILE)

.PHONY: build
build:
	rm -rf target
	mkdir target
	zip -r $(TARGET) ./{*.js,node_modules,package.json,package-lock.json}

.PHONY: publish
publish:
	aws s3 rm s3://$(CODE_DEPLOYMENT_BUCKET)/$(ZIP_FILE)
	aws s3 cp $(TARGET) s3://$(CODE_DEPLOYMENT_BUCKET)/$(ZIP_FILE)

.PHONY: deploy
deploy:
	aws lambda update-function-code \
		--function-name $(shell cat ../../config/iam-policy-templates/cwl-to-elk-exporter-lambda-deployment.json | jq -r '.FunctionName') \
		--s3-bucket $(shell cat ../../config/iam-policy-templates/cwl-to-elk-exporter-lambda-deployment.json | jq -r '.Code.S3Bucket') \
		--s3-key $(shell cat ../../config/iam-policy-templates/cwl-to-elk-exporter-lambda-deployment.json | jq -r '.Code.S3Key')
