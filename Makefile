.PHONY: clean
clean:
	$(MAKE) -C exporters/gcp_to_cwl/ clean

.PHONY: dev
dev:
	$(MAKE) -C exporters/gcp_to_cwl/ dev

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ test

.PHONY: deploy
deploy:
	./setup.sh cloudtrail
	./setup.sh elk
	./setup.sh log-exporter
	./setup.sh gcp-exporter
	$(MAKE) -C exporters/gcp_to_cwl/ deploy
