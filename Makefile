.PHONY: install
install:
	$(MAKE) -C exporters/gcp_to_cwl/ install
	$(MAKE) -C es_managers/es_idx_manager/ install

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ test
	$(MAKE) -C es_managers/es_idx_manager/ test

.PHONY: infrastructure
infrastructure:
	./infrastructure.sh apply

.PHONY: deploy-apps
deploy-apps: deploy-gcp-to-cwl deploy-es-idx-manager deploy-firehose-cwl-processor

.PHONY: deploy-gcp-to-cwl
deploy-gcp-to-cwl:
	DEPLOYMENT_STAGE=staging make -C exporters/gcp_to_cwl/ build deploy

.PHONY: deploy-es-idx-manager
deploy-es-idx-manager:
	DEPLOYMENT_STAGE=staging make -C es_managers/es_idx_manager/ build deploy

.PHONY: deploy-firehose-cwl-processor
deploy-firehose-cwl-processor:
	make -C processors/firehose_to_es_processor/ build publish deploy

.PHONY: encrypt
encrypt:
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in environment -out environment.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in terraform.tfstate -out terraform.tfstate.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in terraform.tfstate.backup -out terraform.tfstate.backup.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in gcp-credentials.json -out gcp-credentials.json.enc
