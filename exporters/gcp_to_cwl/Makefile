export EXPORT_ENV_VARS_TO_LAMBDA=LOG_TOPIC_SUBSCRIPTION_NAME

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
	mkdir -p domovoilib
	cp "$(GOOGLE_APPLICATION_CREDENTIALS)" domovoilib/gcp-credentials.json
	bash -c 'shopt -s nullglob; for wheel in vendor.in/*/*.whl; do unzip -q -o -d vendor $$wheel; done'

.PHONY: deploy
deploy:
	. venv/bin/activate && $(PROJECT_ROOT)/utils/build_deploy_config.sh gcp-to-cwl-exporter $(DEPLOYMENT_STAGE)
	. venv/bin/activate && domovoi deploy --stage $(DEPLOYMENT_STAGE)
