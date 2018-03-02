ZIP_FILE := CWLFirehoseSubscriber_App.zip
TARGET=${PROJECT_ROOT}/subscribers/cwl_firehose_subscriber/target/$(ZIP_FILE)

default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: test
test:
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	rm -rf target
	mkdir target
	zip -r $(TARGET) *.py

.PHONY: init
init:
	[[ -d .terraform ]] || terraform init -backend-config="bucket=$(TERRAFORM_BUCKET)"

.PHONY: deploy
deploy: build
	@terraform apply \
		-var "target_zip_path=${TARGET}" \
		-var "account_id=${ACCOUNT_ID}" \
		-var "blacklisted_log_groups=${BLACKLISTED_LOG_GROUPS}" \
		-auto-approve \
		$([[ "$ACTION" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")
