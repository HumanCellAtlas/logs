.PHONY: install
install:
	virtualenv venv && . venv/bin/activate && pip install -r requirements.txt

terraform-%:
	. venv/bin/activate && ./infrastructure.sh $*

.PHONY: plan
plan: terraform-plan

.PHONY: apply
apply: terraform-apply
