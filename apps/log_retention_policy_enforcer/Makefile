ZIP_FILE := LogRetentionPolicyEnforcer_App.zip
TARGET := target/$(ZIP_FILE)

default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: clean
clean:
	rm -rf target

.PHONY: target
target:
	mkdir -p target

.PHONY: test
test:
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build: target
	cp app.py target/
	cp $(LOG_RETENTION_TTL_FILE) target/
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	cd target && zip -r $(ZIP_FILE) ../*.py ../lib/*.py *

terraform-%:
	. venv/bin/activate && terraform $(*) \
		-var "target_zip_path=$(TARGET)" \
		-var "aws_profile=$(AWS_PROFILE)" \
		$(shell bash -c '[[ "$(*)" == "apply" ]] && echo "-auto-approve" || echo ""')

.PHONY: deploy
deploy: terraform-apply
