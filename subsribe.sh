#!/usr/bin/env bash

# subscribe lambda to cloudwatch and all lambdas
exporters/cwl_to_elk/add_log_group.sh '/aws/cloudtrail/audit-and-data-access'

for group in `aws logs describe-log-groups | jq -r '.logGroups[] | .logGroupName' | egrep '^/(gcp|aws/lambda/)'` ; do
  echo "Subscribing to: $group"
  exporters/cwl_to_elk/add_log_group.sh $group || echo "Subscription failed: $group"
done
