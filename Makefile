.PHONY: infrastructure
infrastructure:
	./infrastructure.sh apply

.PHONY: install
install:
	$(MAKE) -C exporters/gcp_to_cwl/ install
	$(MAKE) -C es_managers/es_idx_manager/ install

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ test
	$(MAKE) -C es_managers/es_idx_manager/ test

.PHONY: deploy
deploy-apps: deploy-gcp-to-cwl deploy-es-idx-manager

.PHONY: deploy-gcp-to-cwl
deploy-gcp-to-cwl:
	DEPLOYMENT_STAGE=staging make -C exporters/gcp_to_cwl/ build deploy

.PHONY: deploy-es-idx-manager
deploy-es-idx-manager:
	DEPLOYMENT_STAGE=staging make -C es_managers/es_idx_manager/ build deploy

.PHONY: encrypt
encrypt:
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/authorized_emails -out config/authorized_emails.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/environment -out config/environment.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/gcp-credentials.json -out config/gcp-credentials.json.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in terraform.tfstate -out terraform.tfstate.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in terraform.tfstate.backup -out terraform.tfstate.backup.enc

