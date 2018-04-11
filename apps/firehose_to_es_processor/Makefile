ZIP_FILE := FirehoseCWLLogsProcessor_App.zip
TARGET := target/$(ZIP_FILE)

default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt --upgrade

.PHONY: test
test:
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	rm -rf target
	mkdir target
	pip install elasticsearch requests_aws4auth retrying airbrake -t . --upgrade
	zip -r $(TARGET) *.py lib/*.py elasticsearch/ urllib3/ certifi/ chardet/ idna/ requests/ requests_aws4auth/ airbrake/

.PHONY: deploy
deploy: build
	. venv/bin/activate && terraform apply \
		-var "target_zip_path=${TARGET}" \
		-var "account_id=${ACCOUNT_ID}" \
		-var "aws_profile=${AWS_PROFILE}" \
		-var "airbrake_blacklisted_log_group_names=${AIRBRAKE_BLACKLISTED_LOG_GROUP_NAMES}" \
		-var "airbrake_whitelisted_log_message_terms=${AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS}" \
		-var "airbrake_flag=${AIRBRAKE_FLAG}" \
		-var "airbrake_api_key=${AIRBRAKE_API_KEY}" \
		-var "airbrake_project_id=${AIRBRAKE_PROJECT_ID}" \
		-var "airbrake_environment=${AIRBRAKE_ENVIRONMENT}" \
		-var "es_endpoint=${ES_ENDPOINT}" \
		-auto-approve \
		$([[ "$ACTION" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")
