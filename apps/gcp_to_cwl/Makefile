ZIP_FILE := GcpToCwlExporter_App.zip
TARGET := target/$(ZIP_FILE)
CREDENTIALS_FILE := target/gcp-credentials.json

default: build

.PHONY: clean
clean:
	rm -rf target

.PHONY: target
target:
	mkdir -p target

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt --upgrade

.PHONY: credentials
credentials:
	aws secretsmanager get-secret-value \
		--secret-id logs/_/gcp_to_cwl.json | \
		jq -r .SecretString | \
		jq .gcp_exporter_google_application_credentials > $(CREDENTIALS_FILE)

.PHONY: test
test: target credentials
	. venv/bin/activate && GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS_FILE) python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build: clean target credentials
	cp app.py target/
	cp -r lib target/
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	bash -c 'shopt -s nullglob; for wheel in vendor.in/*/*.whl; do unzip -q -o -d target $$wheel; done'

.PHONY: deploy
deploy:
	. venv/bin/activate && terraform apply \
		-var-file $(PROJECT_ROOT)/terraform.tfvars \
		-var "target_zip_path=$(TARGET)" \
		-auto-approve
