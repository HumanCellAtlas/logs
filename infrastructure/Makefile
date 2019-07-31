include ../common.mk

.PHONY: plan
plan:
	terraform plan -detailed-exitcode \
	  -var-file $(SECRETS_FILE)

.PHONY: apply
apply:
	terraform apply -var-file $(SECRETS_FILE)
