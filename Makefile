include common.mk

MAKEFILE_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
APPS_REVISION := $(shell git log -n 1 --format="%H" -- apps)
TERRAFORM_BUCKET = org-humancellatlas-$(shell jq -r .account_id $(SECRETS_FILE))-terraform
DEPLOYMENT_STAGE = $(shell jq -r .deployment_stage $(SECRETS_FILE))
DEPLOY_MARKER = s3://$(TERRAFORM_BUCKET)/logs/$(DEPLOYMENT_STAGE)-deployed
APPS := gcp_to_cwl cwl_to_slack es_idx_manager firehose_to_es_processor cwl_firehose_subscriber log_retention_policy_enforcer

.PHONY: secrets check-terraform clean-terraform init init-apps install plan-infra plan-apps test deploy deploy-apps
secrets:
	aws secretsmanager get-secret-value \
		--secret-id logs/_/config.json | \
		jq -r .SecretString | \
		python -m json.tool > $(SECRETS_FILE)
	aws secretsmanager get-secret-value \
		--secret-id logs/_/gcp-credentials-logs-travis.json | \
		jq -r .SecretString | \
		python -m json.tool > gcp-credentials-logs-travis.json


check-terraform:
	bash -c 'if [ "$$(cat infrastructure/.terraform/terraform.tfstate | jq -r .backend.config.profile)" != "$(AWS_PROFILE)" ] ; then echo "AWS profile in local terraform state does not match $(AWS_PROFILE)!" && false ; fi'


## CLEAN
clean-terraform: clean-terraform-infrastructure
	for c in $(APPS); do \
		$(MAKE) clean-terraform-apps.$$c; \
	done

clean-terraform-%:
	cd $(subst .,/,$*)/ && rm -rf .terraform terraform*


## INIT
# terraform init
init: \
	init-infrastructure \
	init-apps

init-apps:
	for c in $(APPS); do \
		$(MAKE) init-apps.$$c; \
	done

init-%:
	cd $(subst .,/,$*)/ && $(MAKEFILE_DIR)/scripts/init.sh


## INSTALL
install:
	for c in $(APPS); do \
		$(MAKE) install-$$c; \
	done

install-%:
	cd apps/$(*)/ && make install


## PLAN
# terraform plan
plan-infrastructure:
	cd infrastructure && make plan

plan-apps:
	for c in $(APPS); do \
		$(MAKE) plan-$$c; \
	done

plan-%:
	cd apps/$(*)/ && make plan


## TEST
test:
	for c in $(APPS); do \
		$(MAKE) test-$$c; \
	done

test-%:
	cd apps/$(*)/ && make test


## DEPLOY
deploy: check-terraform secrets
	cd infrastructure && make apply
	make deploy-apps

deploy-apps:
	for c in $(APPS); do \
		$(MAKE) deploy-$$c; \
	done

deploy-%:
	cd apps/$(*)/ && make build deploy













