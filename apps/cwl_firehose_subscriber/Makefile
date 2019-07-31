include ../../common.mk

ZIP_FILE := CWLFirehoseSubscriber_App.zip
ZIP_PATH := cwl-firehose-subscriber
LAMBDA_BUCKET := `jq -r .logs_lambda_bucket $(SECRETS_FILE)`

default: build


.PHONY: install
install:
	virtualenv -p python3 venv
	venv/bin/pip install -r requirements.txt

.PHONY: plan
plan:
	TF_VAR_path_to_zip_file=$(ZIP_PATH)/$(ZIP_FILE) \
	terraform plan -detailed-exitcode \
	  -var-file $(SECRETS_FILE)

.PHONY: test
test:
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build: install
	rm -rf target
	mkdir target
	venv/bin/pip install -r requirements.txt -t target/ --upgrade
	cp *.py target/
	cd target && zip -r ../$(ZIP_FILE) *

.PHONY: deploy
deploy: build
	aws s3 cp $(ZIP_FILE) s3://$(LAMBDA_BUCKET)/$(ZIP_PATH)/$(ZIP_FILE)
	aws lambda update-function-code --function-name cwl_firehose_subscriber --s3-bucket $(LAMBDA_BUCKET) --s3-key $(ZIP_PATH)/$(ZIP_FILE)
	. venv/bin/activate && TF_VAR_path_to_zip_file=$(ZIP_PATH)/$(ZIP_FILE) \
	    terraform apply -var-file $(SECRETS_FILE)



