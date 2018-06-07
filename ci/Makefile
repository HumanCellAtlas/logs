terraform-%:
	terraform $* \
		-var-file $(PROJECT_ROOT)/terraform.tfvars \
		$(shell [[ "$(*)" == "apply" ]] && echo "-auto-approve" || true)

.PHONY: plan
plan: terraform-plan

.PHONY: apply
apply: terraform-apply
