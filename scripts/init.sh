#!/usr/bin/env bash
TERRAFORM_BUCKET=$(jq -r .terraform_bucket ${PROJECT_ROOT}/terraform.tfvars)
REGION=$(jq -r .aws_region ${PROJECT_ROOT}/terraform.tfvars)

[[ -d .terraform ]] || terraform init \
  -backend-config="bucket=${TERRAFORM_BUCKET}" \
  -backend-config="profile=$AWS_PROFILE" \
  -backend-config="region=$REGION"
