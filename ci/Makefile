terraform-%:
	terraform $* \
		-var "region=$(AWS_REGION)" \
		-var "account_id=$(ACCOUNT_ID)" \
		-var "terraform_bucket=$(TERRAFORM_BUCKET)" \
		$(shell [[ "$(*)" == "apply" ]] && echo "-auto-approve" || true)

.PHONY: plan
plan: terraform-plan

.PHONY: apply
apply: terraform-apply
