ZIP_FILE := EsIndexManager_App.zip
TARGET := target/$(ZIP_FILE)

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
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	cat es-idx-manager-settings.yaml.template | envsubst '$$ES_ENDPOINT' > target/es-idx-manager-settings.yaml
	cp app.py target/
	cd target && zip -r $(ZIP_FILE) ../*.py ../lib/*.py *

terraform-%:
	. venv/bin/activate && terraform $(*) \
		-var "target_zip_path=$(TARGET)" \
		-var "aws_profile=$(AWS_PROFILE)" \
		$([[ "$(*)" == "apply" ]] && echo -n "-auto-approve" || echo -n "") \
		$([[ "$(*)" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")

.PHONY: deploy
deploy: terraform-apply
