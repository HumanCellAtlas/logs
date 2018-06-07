default: build

.PHONY: install
install:
	virtualenv -p python3 venv
	. venv/bin/activate && pip install -r requirements.txt

.PHONY: test
test:
	. venv/bin/activate && python -m unittest discover -s test -p 'test_*.py'

.PHONY: build
build:
	rm -rf target
	mkdir target
	. venv/bin/activate && pip install -r requirements.txt -t target/ --upgrade
	cp *.py target/

.PHONY: deploy
deploy:
	$(MAKE) terraform-apply

terraform-%:
	@terraform $(*) \
		-var-file $(PROJECT_ROOT)/terraform.tfvars \
		-auto-approve \
		$([[ "$(*)" == "plan" ]] && echo -n "-detailed-exitcode" || echo -n "")
