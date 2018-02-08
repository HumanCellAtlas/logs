#!/usr/bin/env bash
TEMPLATE_DIR=${PROJECT_ROOT}/config/iam-policy-templates

aws lambda create-function \
  --cli-input-json "$(cat ${TEMPLATE_DIR}/firehose-cwl-log-processor-lambda-deployment.json | envsubst '$ES_ENDPOINT $ACCOUNT_ID' | sed s/\"/\\\"/g)"
