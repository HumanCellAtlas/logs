ZIP_FILE := FirehoseCWLLogsProcessor_App.zip
TARGET := target/$(ZIP_FILE)

default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt --upgrade

.PHONY: test
test:
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	rm -rf target
	mkdir target
	pip install -r requirements.txt -t target/ --upgrade
	cd target && zip -r $(ZIP_FILE) ../*.py ../lib/*.py *

.PHONY: deploy
deploy: build
	. venv/bin/activate && terraform apply \
		-var "target_zip_path=${TARGET}" \
		-var "account_id=${ACCOUNT_ID}" \
		-var "aws_profile=${AWS_PROFILE}" \
		-var "es_endpoint=${ES_ENDPOINT}" \
		-auto-approve \
		$([[ "$ACTION" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")
