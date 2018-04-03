ZIP_FILE := FirehoseCWLLogsProcessor_App.zip
TARGET := target/$(ZIP_FILE)

default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: test
test:
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	rm -rf target
	mkdir target
	zip -r $(TARGET) *.py lib/*.py

.PHONY: deploy
deploy: build
	@terraform apply \
		-var "target_zip_path=${TARGET}" \
		-var "account_id=${ACCOUNT_ID}" \
		-auto-approve \
		$([[ "$ACTION" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")
