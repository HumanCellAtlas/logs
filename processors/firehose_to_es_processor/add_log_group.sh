aws logs put-subscription-filter \
    --log-group-name "${1}" \
    --filter-name firehose \
    --filter-pattern "" \
    --destination-arn $FIREHOSE_DELIVERY_STREAM_ARN \
    --role-arn $CWL_TO_KINESIS_ROLE_ARN