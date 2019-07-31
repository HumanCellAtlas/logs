#!/usr/bin/env bash
TERRAFORM_BUCKET=$(jq -r .terraform_bucket ${SECRETS_FILE})
REGION=$(jq -r .aws_region ${SECRETS_FILE})

[[ -d .terraform ]] || terraform init \
  -backend-config="bucket=${TERRAFORM_BUCKET}" \
  -backend-config="profile=${AWS_PROFILE}" \
  -backend-config="region=${REGION}"
