terraform-%:
	terraform $* \
		-var "aws_profile=$(AWS_PROFILE)" \
		-var "region=$(AWS_REGION)" \
		-var "account_id=$(ACCOUNT_ID)" \
		-var "terraform_bucket=$(TERRAFORM_BUCKET)" \
		-var "travis_user=$(TRAVIS_USER)" \
		-var "gcp_logs_project_name=$(GCP_LOGS_PROJECT_NAME)" \
		$(shell [[ "$(*)" == "apply" ]] && echo "-auto-approve" || true)

.PHONY: plan
plan: terraform-plan

.PHONY: apply
apply: terraform-apply
