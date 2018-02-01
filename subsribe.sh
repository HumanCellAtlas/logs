#!/usr/bin/env bash

# subscribe lambda to cloudwatch and all lambdas
processors/firehose_to_es_processor/add_log_group.sh '/aws/cloudtrail/audit-and-data-access'

for group in `aws logs describe-log-groups | jq -r '.logGroups[] | .logGroupName' | egrep '^/(gcp|aws/lambda/|aws/batch/)'` ; do
  echo "Subscribing to: $group"
  processors/firehose_to_es_processor/add_log_group.sh $group || echo "Subscription failed: $group"
done
