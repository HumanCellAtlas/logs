include ../../common.mk

SERVICE_NAME := cwl_to_slack
ZIP_FILE := cloudwatch-slack-notifications_App.zip
ZIP_KEY := $(SERVICE_NAME)/$(ZIP_FILE)
LAMBDA_BUCKET := `jq -r .logs_lambda_bucket $(SECRETS_FILE)`

.PHONY: install
install:
	virtualenv -p python3 venv
	venv/bin/pip install -r requirements.txt

terraform-%:
	. venv/bin/activate && terraform $(*) \
		-var-file $(SECRETS_FILE) \
		-var path_to_zip_file=$(ZIP_KEY) \
		-var service_name=$(SERVICE_NAME) \
		$(TF_OPTIONS)

.PHONY: plan
plan:
	TF_OPTIONS=-detailed-exitcode $(MAKE) terraform-plan

.PHONY: test
test:
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'


.PHONY: build
build: install
	rm -rf target
	mkdir target
	cp *.py target/
	venv/bin/pip install -r requirements.txt -t target/ --upgrade
	cd target && zip -r ../$(ZIP_FILE) *


.PHONY: deploy
deploy:
	aws s3 cp $(ZIP_FILE) s3://$(LAMBDA_BUCKET)/$(ZIP_KEY)
	$(MAKE) terraform-apply
	aws lambda update-function-code --function-name cloudwatch-slack-notifier --s3-bucket $(LAMBDA_BUCKET) --s3-key $(ZIP_KEY)
