.PHONY: install
install:
	$(MAKE) -C exporters/gcp_to_cwl/ install
	$(MAKE) -C es_managers/es_idx_manager/ install

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ test
	$(MAKE) -C es_managers/es_idx_manager/ test

.PHONY: infrastructure
infrastructure:
	./infrastructure.sh apply

.PHONY: deploy-apps
deploy-apps: deploy-gcp-to-cwl deploy-es-idx-manager

.PHONY: deploy-gcp-to-cwl
deploy-gcp-to-cwl:
	DEPLOYMENT_STAGE=staging make -C exporters/gcp_to_cwl/ build deploy

.PHONY: deploy-es-idx-manager
deploy-es-idx-manager:
	make -C es_managers/es_idx_manager/ build deploy
