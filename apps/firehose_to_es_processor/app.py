"""
For processing data sent to S3 via firehose by Cloudwatch Logs subscription filters.

Cloudwatch Logs sends to Firehose records that look like this:

{
  "messageType": "DATA_MESSAGE",
  "owner": "123456789012",
  "logGroup": "log_group_name",
  "logStream": "log_stream_name",
  "subscriptionFilters": [
    "subscription_filter_name"
  ],
  "logEvents": [
    {
      "id": "01234567890123456789012345678901234567890123456789012345",
      "timestamp": 1510109208016,
      "message": "log message 1"
    },
    {
      "id": "01234567890123456789012345678901234567890123456789012345",
      "timestamp": 1510109208017,
      "message": "log message 2"
    }
    ...
  ]
}

The data is additionally compressed with GZIP.

The code will:

1) Retrieve the file from S3
2) Gunzip and parse the s3 file into individual records
3) Process/Transform each record and its corresponding log events
4) Bulk send the transformed events to the corresponding elastic search endpoing with today's index
5) Delete the file from s3 after successful processing and post to ES
"""
from lib.firehose_record_processor import FirehoseRecordProcessor
from lib.s3_client import S3Client
from lib.es_client import ESClient


def handler(event, context):
    """Main function"""
    for record in event['Records']:
        region = record['awsRegion']
        bucket = record['s3']['bucket']['name']
        s3_client = S3Client(region, bucket)
        s3_object_key = record['s3']['object']['key']
        file = s3_client.retrieve_file(s3_object_key)
        input_records = s3_client.unzip_and_parse_firehose_s3_file(file)

        firehose_record_processor = FirehoseRecordProcessor(input_records)
        firehose_record_processor.run()

        es_client = ESClient()
        es_client.create_cwl_day_index()
        es_client.bulk_post(firehose_record_processor.output_records)

        s3_client.delete_file(s3_object_key)
