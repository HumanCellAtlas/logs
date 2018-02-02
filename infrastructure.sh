#!/usr/bin/env bash

ACTION=$1

[[ "$ACTION" != "apply" && "$ACTION" != "plan" ]] && echo "usage: $0 {apply,plan}" && exit 1

terraform "$ACTION" \
  -var "account_id=${ACCOUNT_ID}" \
  -var "cloudtrail_log_group_name=${CLOUDTRAIL_LOG_GROUP_NAME}" \
  -var "cloudtrail_name=${CLOUDTRAIL_NAME}" \
  -var "es_email_principals=${ES_AUTHORIZED_EMAILS}" \
  -var "cloudtrail_s3_bucket=${CLOUDTRAIL_S3_BUCKET}" \
  -var "es_domain_name=${ES_DOMAIN_NAME}"
