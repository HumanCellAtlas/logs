#!/usr/bin/env bash
[[ -d .terraform ]] || terraform init \
  -backend-config="bucket=$TERRAFORM_BUCKET" \
  -backend-config="profile=$AWS_PROFILE" \
  -backend-config="region=$AWS_DEFAULT_REGION"
