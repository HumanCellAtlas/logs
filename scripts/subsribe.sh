#!/usr/bin/env bash

firehose_delivery_stream_arn=$(aws firehose describe-delivery-stream --delivery-stream-name ${1} | jq -r '.DeliveryStreamDescription.DeliveryStreamARN')
cwl_to_kinesis_role_arn="arn:aws:iam::${ACCOUNT_ID}:role/${2}"

# subscribe lambda to cloudwatch and all lambdas
processors/firehose_to_es_processor/add_log_group.sh '/aws/cloudtrail/audit-and-data-access' $firehose_delivery_stream_arn $cwl_to_kinesis_role_arn

for group in `aws logs describe-log-groups | jq -r '.logGroups[] | .logGroupName' | egrep '^/(gcp|aws/lambda/|aws/batch/)'` ; do
  echo "Subscribing to: $group"
  processors/firehose_to_es_processor/add_log_group.sh $group $firehose_delivery_stream_arn $cwl_to_kinesis_role_arn || echo "Subscription failed: $group"
done