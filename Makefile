.PHONY: clean
clean:
	$(MAKE) -C exporters/gcp_to_cwl/ clean

.PHONY: dev
dev:
	$(MAKE) -C exporters/gcp_to_cwl/ dev

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ test

.PHONY: deploy-infra
deploy-infra:
	./setup.sh cloudtrail
	./setup.sh elk
	./setup.sh configure-log-exporter
	./setup.sh configure-gcp-exporter

.PHONY: deploy-apps
deploy-apps:
	DEPLOYMENT_STAGE=staging make -C exporters/gcp_to_cwl/ build deploy
	make -C exporters/cwl_to_elk/ build publish deploy
	make -C es_managers/es_idx_manager/ build deploy
