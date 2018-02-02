.PHONY: dev
dev:
	$(MAKE) -C exporters/gcp_to_cwl/ dev
	$(MAKE) -C es_managers/es_idx_manager/ dev

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ test
	$(MAKE) -C es_managers/es_idx_manager/ test

.PHONY: deploy-infra
deploy-infra:
	./setup.sh cloudtrail
	./setup.sh elk
	./setup.sh configure-gcp-exporter
	./setup.sh configure-firehose-cwl-processor
	./setup.sh kinesis-firehose-stream
	./setup.sh cwl-to-firehose-stream

.PHONY: deploy-apps
deploy-apps:
	DEPLOYMENT_STAGE=staging make -C exporters/gcp_to_cwl/ build deploy
	make -C es_managers/es_idx_manager/ build deploy
	make -C processors/firehose_to_es_processor/ build publish deploy
