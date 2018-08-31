terraform-%:
	terraform $* \
		-var-file $(PROJECT_ROOT)/terraform.tfvars

.PHONY: plan
plan: terraform-plan

.PHONY: apply
apply: terraform-apply
