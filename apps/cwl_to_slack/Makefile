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
		-var "slack_webhook_url=$(SLACK_WEBHOOK_URL)" \
		-var "slack_alert_channel=$(SLACK_ALERT_CHANNEL)" \
		$(shell [[ $(*) == "apply" ]] && echo "-auto-approve" || true)

.PHONY: plan
plan: terraform-plan

.PHONY: deploy
deploy: terraform-apply
