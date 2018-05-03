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
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	cd target && zip -r $(ZIP_FILE) ../*.py ../lib/*.py *

.PHONY: deploy
deploy:
	. venv/bin/activate && terraform apply \
		-var "target_zip_path=$(TARGET)" \
		-var "account_id=$(ACCOUNT_ID)" \
		-var "aws_profile=$(AWS_PROFILE)" \
		-var "es_endpoint=$(ES_ENDPOINT)" \
		-var "airbrake_blacklisted_log_group_names=$(AIRBRAKE_BLACKLISTED_LOG_GROUP_NAMES)" \
		-var "airbrake_whitelisted_log_message_terms=$(AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS)" \
		-var "airbrake_blacklisted_log_message_strings=$(AIRBRAKE_BLACKLISTED_LOG_MESSAGE_STRINGS)" \
		-var "airbrake_flag=$(AIRBRAKE_FLAG)" \
		-var "airbrake_api_key=$(AIRBRAKE_API_KEY)" \
		-var "airbrake_project_id=$(AIRBRAKE_PROJECT_ID)" \
		-var "airbrake_environment=$(AIRBRAKE_ENVIRONMENT)" \
		-auto-approve \
		$(shell [[ "$ACTION" == "plan" ]] && echo "-detailed-exitcode" || echo "")
