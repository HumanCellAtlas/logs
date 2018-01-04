.PHONY: image
image:
	docker build -t ubuntu-nodejs .

.PHONY: clean
clean:
	rm -rf node_modules

.PHONY: dev
dev: clean
	npm install

.PHONY: install
install:
	docker run -it \
		-v `pwd`/:/tmp/ \
		ubuntu-nodejs:latest \
		bash -c 'cd /tmp && make clean && npm install `jq -r ".dependencies | keys[]" package.json | egrep -v "mocha|sinon|should"`'

.PHONY: test
test:
	npm test

.PHONY: deploy
deploy:
	gcloud beta functions deploy exportLogs --trigger-bucket hca-logs
