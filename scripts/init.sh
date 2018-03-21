#!/usr/bin/env bash
[[ -d .terraform ]] || terraform init -backend-config="bucket=$TERRAFORM_BUCKET" -backend-config="region=$AWS_REGION"
