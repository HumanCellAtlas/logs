include ../common.mk
SERVICE_NAME := logs-infra

.PHONY: plan
plan:
	terraform plan -detailed-exitcode \
	  -var-file $(SECRETS_FILE) \
	  -var service_name=$(SERVICE_NAME)

.PHONY: apply
apply:
	terraform apply \
		-var-file $(SECRETS_FILE) \
		-var service_name=$(SERVICE_NAME)
