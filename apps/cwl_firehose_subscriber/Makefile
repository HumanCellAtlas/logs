ZIP_FILE := CWLFirehoseSubscriber_App.zip
TARGET=target/$(ZIP_FILE)
MAKEFILE_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

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

.PHONY: deploy
deploy:
	$(MAKE) terraform-apply

terraform-%:
	@terraform $(*) \
		-var "target_zip_path=$(MAKEFILE_DIR)/$(TARGET)" \
		-var "account_id=$(ACCOUNT_ID)" \
		-var "aws_profile=$(AWS_PROFILE)" \
		-var "aws_region=$(AWS_REGION)" \
		-var "blacklisted_log_groups=$(BLACKLISTED_LOG_GROUPS)" \
		-auto-approve \
		$([[ "$(*)" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")
