.PHONY: clean
clean:
	$(MAKE) -C queue_logs clean
	$(MAKE) -C batch_export_logs clean
	$(MAKE) -C timer clean

.PHONY: install
install:
	$(MAKE) -C queue_logs install
	$(MAKE) -C batch_export_logs install
	$(MAKE) -C timer install

.PHONY: test
test:
	$(MAKE) -C queue_logs test
	$(MAKE) -C batch_export_logs test

.PHONY: deploy
deploy:
	$(MAKE) -C queue_logs deploy
	$(MAKE) -C batch_export_logs deploy
	$(MAKE) -C timer deploy
