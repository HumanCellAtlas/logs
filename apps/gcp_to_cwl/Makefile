export EXPORT_ENV_VARS_TO_LAMBDA=
CREDENTIALS_FILE = domovoilib/gcp-credentials.json

default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: credentials
credentials:
	aws secretsmanager get-secret-value \
		--secret-id logs/_/gcp_to_cwl.json | \
		jq -r .SecretString | \
		jq .gcp_exporter_google_application_credentials > domovoilib/gcp-credentials.json

.PHONY: test
test: credentials
	. venv/bin/activate && GOOGLE_APPLICATION_CREDENTIALS=$(CREDENTIALS_FILE) python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build: credentials
	mkdir -p domovoilib
	bash -c 'shopt -s nullglob; for wheel in vendor.in/*/*.whl; do unzip -q -o -d vendor $$wheel; done'

.PHONY: deploy
deploy:
	. venv/bin/activate && $(PROJECT_ROOT)/scripts/build_deploy_config.sh gcp-to-cwl-exporter $(DEPLOYMENT_STAGE)
	. venv/bin/activate && domovoi deploy --stage $(DEPLOYMENT_STAGE)
