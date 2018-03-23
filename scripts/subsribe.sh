#!/usr/bin/env bash

firehose_delivery_stream_arn=$(aws firehose describe-delivery-stream --delivery-stream-name ${1} | jq -r '.DeliveryStreamDescription.DeliveryStreamARN')
cwl_to_kinesis_role_arn="arn:aws:iam::${ACCOUNT_ID}:role/${2}"

echo "$firehose_delivery_stream_arn"
echo "$cwl_to_kinesis_role_arn"

# subscribe lambda to cloudwatch and all lambdas
processors/firehose_to_es_processor/add_log_group.sh $CLOUDTRAIL_LOG_GROUP_NAME $firehose_delivery_stream_arn $cwl_to_kinesis_role_arn

for group in `aws logs describe-log-groups | jq -r '.logGroups[] | .logGroupName'` ; do
  echo "Subscribing to: $group"
  processors/firehose_to_es_processor/add_log_group.sh $group $firehose_delivery_stream_arn $cwl_to_kinesis_role_arn || echo "Subscription failed: $group"
done