.PHONY: clean
clean:
	rm -rf node_modules

.PHONY: install
install:
	npm install

.PHONY: test
test:
	npm test

.PHONY: deploy
deploy:
	yes | gcloud beta functions delete queueLogs || true
	gcloud beta functions deploy queueLogs --trigger-topic logs

