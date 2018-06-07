ZIP_FILE := EsIndexManager_App.zip
TARGET := target/$(ZIP_FILE)
ES_IDX_MANAGER_SETTINGS := target/es-idx-manager-settings.yaml

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
	. venv/bin/activate && \
		ES_IDX_MANAGER_SETTINGS=es-idx-manager-settings.yaml \
		python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	cp es-idx-manager-settings.yaml $(ES_IDX_MANAGER_SETTINGS)
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	cp app.py target/
	cd target && zip -r $(ZIP_FILE) ../*.py ../lib/*.py *

terraform-%:
	. venv/bin/activate && terraform $(*) \
		-var "target_zip_path=$(TARGET)" \
		-var "aws_profile=$(AWS_PROFILE)" \
		$(shell [[ "$(*)" == "apply" ]] && echo "-auto-approve" || echo "")

.PHONY: deploy
deploy: terraform-apply
