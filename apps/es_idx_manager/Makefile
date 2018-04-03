export EXPORT_ENV_VARS_TO_LAMBDA=
ES_ENDPOINT := $(shell aws es describe-elasticsearch-domain --domain $$ES_DOMAIN_NAME | jq -r '.DomainStatus.Endpoint')

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
	cp "$(ES_IDX_MANAGER_SETTINGS)" domovoilib/es-idx-manager-settings.yaml

.PHONY: deploy
deploy: build
	. venv/bin/activate && $(PROJECT_ROOT)/scripts/build_deploy_config.sh es-idx-manager $(DEPLOYMENT_STAGE)
	. venv/bin/activate && domovoi deploy --stage $(DEPLOYMENT_STAGE)
