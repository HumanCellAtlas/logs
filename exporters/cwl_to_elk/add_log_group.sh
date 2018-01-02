#!/usr/bin/env bash

aws logs put-subscription-filter \
  --log-group-name "${1}" \
  --filter-name allLogs \
  --filter-pattern "" \
  --destination-arn arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:LogsToElasticsearch
