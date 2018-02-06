#!/usr/bin/env bash

# subscribe lambda to cloudwatch and all lambdas
$PROJECT_ROOT/exporters/cwl_to_elk/add_log_group.sh "$CLOUDTRAIL_LOG_GROUP_NAME"

for group in `aws logs describe-log-groups | jq -r '.logGroups[] | .logGroupName' | egrep '^/(gcp|aws/lambda/|aws/batch/)'` ; do
  echo "Subscribing to: $group"
  exporters/cwl_to_elk/add_log_group.sh $group || echo "Subscription failed: $group"
done
