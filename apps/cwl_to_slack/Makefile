TARGET := cloudwatch-slack-notifications_App.zip

.PHONY: clean
clean:
	rm -rf $(TARGET)

.PHONY: build
build:
	rm -rf target
	mkdir target
	npm install
	zip -r $(TARGET) *.js package-lock.json

terraform-%:
	@terraform $(*) \
		-var "aws_region=$(AWS_REGION)" \
		-var "aws_profile=$(AWS_PROFILE)" \
		-var "target_zip_path=$(TARGET)" \
		-var "kms_key_arn=$(KMS_KEY_ARN)"

.PHONY: plan
plan: terraform-plan

.PHONY: deploy
deploy: terraform-apply
