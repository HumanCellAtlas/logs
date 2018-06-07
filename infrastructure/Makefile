terraform-%:
	terraform $(*) \
		-var-file $(PROJECT_ROOT)/terraform.tfvars \
		$([[ "$ACTION" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")

.PHONY: plan
plan: terraform-plan

.PHONY: apply
apply: terraform-apply
