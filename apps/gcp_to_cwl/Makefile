include ../../common.mk

SERVICE_NAME := gcp-to-cwl
ZIP_FILE := GcpToCwlExporter_App.zip
ZIP_KEY := $(SERVICE_NAME)/$(ZIP_FILE)
CREDENTIALS_FILE := target/gcp-credentials.json
LAMBDA_BUCKET := `jq -r .logs_lambda_bucket $(SECRETS_FILE)`


default: build

.PHONY: clean
clean:
	rm -rf target/
	rm -f *.zip

.PHONY: target
target:
	mkdir -p target

.PHONY: credentials
credentials:
	aws secretsmanager get-secret-value \
		--secret-id logs/_/gcp-credentials-logs-travis.json | \
		jq -r .SecretString > $(CREDENTIALS_FILE)


.PHONY: install
install:
	virtualenv -p python3 venv
	venv/bin/pip install -r requirements.txt --upgrade

terraform-%:
	. venv/bin/activate && terraform $(*) \
		-var-file $(SECRETS_FILE) \
		-var path_to_zip_file=$(ZIP_KEY) \
		-var service_name=$(SERVICE_NAME) \
		$(TF_OPTIONS)

.PHONY: plan
plan:
	TF_OPTIONS=-detailed-exitcode $(MAKE) terraform-plan

.PHONY: test
test: credentials
	rm -rf target
	mkdir target
	. venv/bin/activate && GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS_FILE) python -m unittest discover -s test -p 'test_*.py'


.PHONY: build
build: clean target install credentials
	cp app.py target/
	cp -r lib target/
	venv/bin/pip install -r requirements.txt -t target/ --upgrade
	bash -c 'shopt -s nullglob; for wheel in vendor.in/*/*.whl; do unzip -q -o -d target $$wheel; done'
	cd target && zip -r ../$(ZIP_FILE) *


.PHONY: deploy
deploy:
	aws s3 cp $(ZIP_FILE) s3://$(LAMBDA_BUCKET)/$(ZIP_KEY)
	$(MAKE) terraform-apply
	aws lambda update-function-code --function-name gcp-to-cwl-exporter --s3-bucket $(LAMBDA_BUCKET) --s3-key $(ZIP_KEY)


