TARGET := cloudwatch-slack-notifications_App.zip

.PHONY: clean
clean:
	rm -rf $(TARGET)

.PHONY: build
build:
	rm -rf target
	mkdir target
	npm install
	zip -r $(TARGET) *.js package-lock.json

terraform-%:
	@terraform $(*) \
		-var-file "$(PROJECT_ROOT)/terraform.tfvars" \
		$(shell [[ $(*) == "apply" ]] && echo "-auto-approve" || true)

.PHONY: plan
plan: terraform-plan

.PHONY: deploy
deploy: terraform-apply
