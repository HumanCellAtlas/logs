SHELL=/bin/bash

ifndef SECRETS_FILE
$(error Please run "source environment" in the repo root directory before running make commands)
endif

ifndef PROJECT_ROOT
$(error Please run "source environment" in the repo root directory before running make commands)
endif
