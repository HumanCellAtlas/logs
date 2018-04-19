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
import logging
import os

from lib import firehose_records
from lib.airbrake_notifier import AirbrakeNotifier
from lib.s3_client import S3Client
from lib.es_client import ESClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

record_callbacks = []

# record callback configuration
if os.environ.get('AIRBRAKE_FLAG', None) == 'True':
    record_callbacks += [AirbrakeNotifier.notify]
    logger.info("Airbrake notifier enabled!")


def handler(event, context):
    """Main function"""
    for record in event['Records']:
        region = record['awsRegion']
        bucket = record['s3']['bucket']['name']
        s3_client = S3Client(region, bucket)
        s3_object_key = record['s3']['object']['key']
        file = s3_client.retrieve_file(s3_object_key)

        doc_stream = s3_client.unzip_and_parse_firehose_s3_file(file)
        record_stream = firehose_records.from_docs(doc_stream)

        es_client = ESClient()
        es_client.create_cwl_day_index()
        es_client.bulk_post(list(record_stream))

        s3_client.delete_file(s3_object_key)
