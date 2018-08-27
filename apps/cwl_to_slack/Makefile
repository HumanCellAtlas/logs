ZIP_FILE := cloudwatch-slack-notifications_App.zip

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt


.PHONY: build
build:
	rm -rf target
	mkdir target
	cp *.py target/
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	cd target && zip -r ../$(ZIP_FILE) *


terraform-%:
	@terraform $(*) \
		-var-file "$(PROJECT_ROOT)/terraform.tfvars" \
		$(shell [[ $(*) == "apply" ]] && echo "-auto-approve" || true)

.PHONY: plan
plan: terraform-plan

.PHONY: deploy
deploy: terraform-apply
	aws s3 cp $(ZIP_FILE) s3://org-hca-logs-lambda-deployment/cwl_to_slack/$(ZIP_FILE)
	aws lambda update-function-code --function-name cloudwatch-slack-notifier --s3-bucket org-hca-logs-lambda-deployment --s3-key cwl_to_slack/$(ZIP_FILE)

