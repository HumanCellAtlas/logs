.PHONY: install
install:
	virtualenv venv && . venv/bin/activate && pip install -r requirements.txt
	$(MAKE) -C apps/gcp_to_cwl/ install
	$(MAKE) -C apps/es_idx_manager/ install
	$(MAKE) -C apps/cwl_firehose_subscriber/ install
	$(MAKE) -C apps/firehose_to_es_processor/ install

.PHONY: image
image:
	docker build -t trusty-python3 .

.PHONY: test
test:
	$(MAKE) -C apps/gcp_to_cwl/ test
	$(MAKE) -C apps/es_idx_manager/ test
	$(MAKE) -C apps/cwl_firehose_subscriber/ test
	$(MAKE) -C apps/firehose_to_es_processor/ test

.PHONY: init
init:
	terraform init -backend-config="bucket=$(TERRAFORM_BUCKET)"

.PHONY: infrastructure
infrastructure:
	./infrastructure.sh apply

.PHONY: deploy
deploy-apps: deploy-gcp-to-cwl deploy-es-idx-manager deploy-cwl-to-slack-notifier deploy-cwl-firehose-subscriber deploy-firehose-cwl-processor

.PHONY: deploy-gcp-to-cwl
deploy-gcp-to-cwl:
	DEPLOYMENT_STAGE=staging $(MAKE) -C apps/gcp_to_cwl/ build deploy

.PHONY: deploy-cwl-to-slack-notifier
deploy-cwl-to-slack-notifier:
	DEPLOYMENT_STAGE=staging $(MAKE) -C apps/cwl_to_slack/ build init deploy

.PHONY: deploy-es-idx-manager
deploy-es-idx-manager:
	DEPLOYMENT_STAGE=staging $(MAKE) -C apps/es_idx_manager/ build deploy

.PHONY: deploy-firehose-cwl-processor
deploy-firehose-cwl-processor:
	$(MAKE) -C apps/firehose_to_es_processor/ build init deploy

.PHONY: deploy-cwl-firehose-subscriber
deploy-cwl-firehose-subscriber:
	$(MAKE) -C apps/cwl_firehose_subscriber/ build init deploy

.PHONY: encrypt
encrypt:
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/authorized_emails -out config/authorized_emails.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/environment -out config/environment.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/gcp-credentials.json -out config/gcp-credentials.json.enc
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/ES_IDX_MANAGER_SETTINGS.yaml -out config/ES_IDX_MANAGER_SETTINGS.yaml.enc

.PHONY: decrypt
decrypt:
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/authorized_emails.enc -out config/authorized_emails -d
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/environment.enc -out config/environment -d
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/gcp-credentials.json.enc -out config/gcp-credentials.json -d
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/ES_IDX_MANAGER_SETTINGS.yaml.enc -out config/ES_IDX_MANAGER_SETTINGS.yaml -d
