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

.PHONY: init
init:
	[[ -d .terraform ]] || terraform init -backend-config="bucket=$(TERRAFORM_BUCKET)"

.PHONY: plan
plan:
	@terraform plan \
		-var "account_id=$(ACCOUNT_ID)" \
		-var "target_zip_path=$(TARGET)" \
		-var "kms_key_arn=$(KMS_KEY_ARN)"

.PHONY: deploy
deploy:
	@terraform apply \
		-var "account_id=$(ACCOUNT_ID)" \
		-var "target_zip_path=$(TARGET)" \
		-var "kms_key_arn=$(KMS_KEY_ARN)" \
		-auto-approve
