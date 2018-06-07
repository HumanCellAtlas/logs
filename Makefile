MAKEFILE_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
APPS_REVISION := $(shell git log -n 1 --format="%H" -- apps)
TERRAFORM_BUCKET = org-humancellatlas-$(shell jq -r .account_id terraform.tfvars)-terraform
DEPLOYMENT_STAGE = $(shell jq -r .deployment_stage terraform.tfvars)
DEPLOY_MARKER = s3://$(TERRAFORM_BUCKET)/logs/$(DEPLOYMENT_STAGE)-deployed

.PHONY: secrets
secrets:
	aws secretsmanager get-secret-value \
		--secret-id logs/_/config.json | \
		jq -r .SecretString | \
		python -m json.tool > terraform.tfvars
	aws secretsmanager get-secret-value \
		--secret-id logs/_/gcp-credentials-logs-travis.json | \
		jq -r .SecretString | \
		python -m json.tool > gcp-credentials-logs-travis.json

.PHONY: rev
rev:
	echo $(APPS_REVISION)

# terraform init
init-%:
	cd $(subst .,/,$*)/ && $(MAKEFILE_DIR)/scripts/init.sh

.PHONY: init
init: \
	init-infrastructure \
	init-apps.cwl_to_slack \
	init-apps.es_idx_manager \
	init-apps.firehose_to_es_processor \
	init-apps.cwl_firehose_subscriber \
	init-ci

clean-terraform-%:
	cd $(subst .,/,$*)/ && rm -rf .terraform terraform*

.PHONY: clean-terraform
clean-terraform: \
	clean-terraform-infrastructure \
	clean-terraform-apps.cwl_to_slack \
	clean-terraform-apps.es_idx_manager \
	clean-terraform-apps.firehose_to_es_processor \
	clean-terraform-apps.cwl_firehose_subscriber \
	clean-terraform-ci

# infrastructure
infrastructure-%:
	cd infrastructure && make $*

# apps
install-%:
	$(MAKE) -C $(subst .,/,$*)/ install

.PHONY: install
install: \
	install-apps.gcp_to_cwl \
	install-apps.es_idx_manager \
	install-apps.cwl_firehose_subscriber \
	install-apps.firehose_to_es_processor

test-%:
	$(MAKE) -C $(subst .,/,$*)/ test

.PHONY: test
test: \
	test-apps.gcp_to_cwl \
	test-apps.es_idx_manager \
	test-apps.cwl_firehose_subscriber \
	test-apps.firehose_to_es_processor

deploy-%:
	$(MAKE) -C apps/$(*)/ build deploy

.PHONY: deploy
deploy: \
	deploy-gcp_to_cwl \
	deploy-es_idx_manager \
	deploy-cwl_to_slack \
	deploy-cwl_firehose_subscriber \
	deploy-firehose_to_es_processor
	echo $(APPS_REVISION) > /tmp/rev
	aws s3 cp /tmp/rev $(DEPLOY_MARKER)

.PHONY: is-deployed
is-deployed:
	aws s3 cp $(DEPLOY_MARKER) /tmp/rev
	bash -c '[[ `cat /tmp/rev` == "$(APPS_REVISION)" ]]'

# prod deployment
.PHONY: prod-deploy
prod-deploy:
ifneq ($(shell cat infrastructure/.terraform/terraform.tfstate | jq -r '.backend.config.profile'),hca-prod)
	$(MAKE) clean-terraform
	. config/environment_prod && $(MAKE) init
endif
	. config/environment_prod && cd infrastructure && make apply
	. config/environment_prod && $(MAKE) deploy

# dev deployment
.PHONY: dev-deploy
dev-deploy:
ifneq ($(shell cat infrastructure/.terraform/terraform.tfstate | jq -r '.backend.config.profile'),hca)
	$(MAKE) clean-terraform
	. config/environment_dev && $(MAKE) init
endif
	. config/environment_dev && cd infrastructure && make apply
	. config/environment_dev && $(MAKE) deploy
