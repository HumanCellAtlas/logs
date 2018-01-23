export EXPORT_ENV_VARS_TO_LAMBDA=LOG_TOPIC_SUBSCRIPTION_NAME

default: build

.PHONY: clean
clean:
	rm -rf node_modules

.PHONY: dev
dev: clean
	npm install

.PHONY: test
test:
	python3 -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	mkdir -p domovoilib
	cp "$(GOOGLE_APPLICATION_CREDENTIALS)" domovoilib/gcp-credentials.json
	shopt -s nullglob; for wheel in vendor.in/*/*.whl; do unzip -q -o -d vendor $$wheel; done

.PHONY: deploy
deploy: build
	./build_deploy_config.sh gcp-to-cwl-exporter $(DEPLOYMENT_STAGE)
	domovoi deploy --stage $(DEPLOYMENT_STAGE)
