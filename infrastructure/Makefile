.PHONY: plan
plan:
	terraform plan -detailed-exitcode \
	  -var-file $(PROJECT_ROOT)/terraform.tfvars

.PHONY: apply
apply:
	terraform apply -var-file $(PROJECT_ROOT)/terraform.tfvars
