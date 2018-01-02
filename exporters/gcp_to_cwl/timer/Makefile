default: install

clean:
	rm -rf lib

install:
	mkdir -p lib/
	pip install -t lib/ -r requirements.txt

deploy:
	yes | gcloud app deploy app.yaml
