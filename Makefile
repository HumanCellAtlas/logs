MAKEFILE_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

# terraform init
init-%:
	cd $(subst .,/,$*)/ && $(MAKEFILE_DIR)/scripts/init.sh

.PHONY: init
init: init-infrastructure init-apps.cwl_to_slack init-apps.firehose_to_es_processor init-apps.cwl_firehose_subscriber init-ci

clean-terraform-%:
	cd $(subst .,/,$*)/ && rm -rf .terraform terraform*

.PHONY: clean-terraform
clean-terraform: clean-terraform-infrastructure clean-terraform-apps.cwl_to_slack clean-terraform-apps.firehose_to_es_processor clean-terraform-apps.cwl_firehose_subscriber clean-terraform-ci

# infrastructure

infrastructure-%:
	cd infrastructure && make $*

# apps
install-%:
	$(MAKE) -C $(subst .,/,$*)/ install

.PHONY: install
install: install-apps.gcp_to_cwl install-apps.es_idx_manager install-apps.cwl_firehose_subscriber install-apps.firehose_to_es_processor

test-%:
	$(MAKE) -C $(subst .,/,$*)/ test

.PHONY: test
test: test-apps.gcp_to_cwl test-apps.es_idx_manager test-apps.cwl_firehose_subscriber test-apps.firehose_to_es_processor

deploy-%:
	$(MAKE) -C apps/$(*)/ build deploy

.PHONY: deploy
deploy: deploy-gcp_to_cwl deploy-es_idx_manager deploy-cwl_to_slack deploy-cwl_firehose_subscriber deploy-firehose_to_es_processor

# secrets
encrypt-%:
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/$(*) -out config/$(*).enc

decrypt-%:
	openssl aes-256-cbc -k "$(ENCRYPTION_KEY)" -in config/$(*).enc -out config/$(*) -d

encrypt: encrypt-environment_staging encrypt-environment_prod encrypt-ES_IDX_MANAGER_SETTINGS.yaml encrypt-authorized_emails encrypt-gcp-credentials-staging.json decrypt-gcp-credentials-prod.json encrypt-authorized_pubsub_publishers_staging

.PHONY: decrypt
decrypt: decrypt-environment_staging decrypt-environment_prod decrypt-ES_IDX_MANAGER_SETTINGS.yaml decrypt-authorized_emails decrypt-gcp-credentials-staging.json decrypt-gcp-credentials-prod.json decrypt-authorized_pubsub_publishers_staging

# prod deployment
.PHONY: prod-deploy
prod-deploy:
ifneq ($(shell cat infrastructure/.terraform/terraform.tfstate | jq -r '.backend.config.profile'),hca-prod)
	$(MAKE) clean-terraform
	. config/environment_prod && $(MAKE) init
endif
	. config/environment_prod && cd infrastructure && make apply
	. config/environment_prod && $(MAKE) deploy
