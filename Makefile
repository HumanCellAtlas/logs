.PHONY: image
image:
	docker build -t ubuntu-nodejs .

.PHONY: clean
clean:
	$(MAKE) -C exporters/gcp_to_cwl/ clean

.PHONY: install
install: image
	$(MAKE) -C exporters/gcp_to_cwl/ install

.PHONY: test
test:
	$(MAKE) -C exporters/gcp_to_cwl/ clean dev test

.PHONY: deploy
deploy:
	./setup.sh cloudtrail
	./setup.sh elk
	./setup.sh log-exporter
	./setup.sh gcp-exporter
	$(MAKE) -C exporters/gcp_to_cwl/ deploy
