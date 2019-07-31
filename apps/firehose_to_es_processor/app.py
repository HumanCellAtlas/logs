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
import sys

from lib import firehose_records
from lib.airbrake_notifier import AirbrakeNotifier
from lib.cloudwatch_notifier import observe_counts
from lib.s3_client import S3Client
from lib.es_client import ESClient
from lib.secrets import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

AIRBRAKE_ENABLED = config['airbrake_enabled']


def handler(event, context):
    """Main function"""
    for record in event['Records']:
        region = record['awsRegion']
        bucket = record['s3']['bucket']['name']
        s3_client = S3Client(region, bucket)
        s3_object_key = record['s3']['object']['key']
        logger.info(f"Loading from s3 file {s3_object_key}")
        file = s3_client.retrieve_file(s3_object_key)['Body']

        doc_stream = s3_client.unzip_and_parse_firehose_file(file)
        log_event_stream = firehose_records.from_docs(doc_stream)

        notifier = None
        if AIRBRAKE_ENABLED:
            notifier = AirbrakeNotifier()
            log_event_stream = notifier.notify_on_stream(log_event_stream)

        es_client = ESClient()
        es_client.create_cwl_day_index()

        current_stream_size = 0
        batch = []
        total_lines = 0
        # buffer up to 25MB at a time and then submit to Elasticsearch
        for log_event in log_event_stream:
            current_stream_size += sys.getsizeof(log_event)
            batch.append(log_event)
            total_lines += 1
            if current_stream_size > 25000000:
                es_client.bulk_post(batch)
                current_stream_size = 0
                batch = []

        if len(batch) > 0:
            es_client.bulk_post(batch)

        s3_client.delete_file(s3_object_key)

        if notifier:
            report = notifier.report()
            observe_counts(report)
            for log_group, counts in notifier._report.items():
                logger.info("Observed log group {}: {} total, {} errors".format(
                        log_group,
                        counts['total'],
                        counts['errors']
                    )
                )

        logger.info("Indexed {} log events".format(total_lines))
