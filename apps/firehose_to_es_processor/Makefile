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
		-var-file $(PROJECT_ROOT)/terraform.tfvars \
		-var "target_zip_path=$(TARGET)" \
		-auto-approve
