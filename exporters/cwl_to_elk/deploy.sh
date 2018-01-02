#!/usr/bin/env bash
TEMPLATE_DIR=../../config/iam-policy-templates

aws lambda create-function \
  --cli-input-json "$(cat ${TEMPLATE_DIR}/cwl-to-elk-exporter-lambda-deployment.json | envsubst '$ES_ENDPOINT $ELK_EXPORT_ROLE_ARN' | sed s/\"/\\\"/g)" \
  || echo "Lambda function already exists!"
aws lambda add-permission \
  --cli-input-json "$(cat ${TEMPLATE_DIR}/lambda_permission.json | envsubst '$ACCOUNT_ID' | sed s/\"/\\\"/g)" \
  || echo "Permission already exists!"
