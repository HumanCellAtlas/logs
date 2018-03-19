"""
For processing data sent to Firehose by Cloudwatch Logs subscription filters.

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

1) Gunzip the data
2) Parse the json
3) Set the result to Dropped for any record whose messageType is not DATA_MESSAGE. Such records do not contain any log events.
4) For records whose messageType is DATA_MESSAGE, extract the individual log events from the logEvents field, and pass
   each one to the transform_log_event method. Individual parents with more than one children log records are transformed, encoded, and requeued for ingestion.
5) Transformed records are sent back to kinesis firehose ready for the final destination.
6) Any additional records which exceed 6MB will be re-ingested back into Firehose.

"""

import boto3
from lib.firehose_record_processor import FirehoseRecordProcessor
from lib.firehose_record_transmitter import FirehoseRecordTransmitter


def handler(event, context):
    """Main function"""

    input_records = event['records']
    firehose_record_processor = FirehoseRecordProcessor(input_records)
    firehose_record_processor.run()

    records_to_reingest = firehose_record_processor.records_to_reingest
    if len(records_to_reingest) > 0:
        stream_arn = event['deliveryStreamArn']
        region = stream_arn.split(':')[3]
        stream_name = stream_arn.split('/')[1]
        FirehoseRecordTransmitter(region, stream_name, records_to_reingest).transmit()

    output_records = firehose_record_processor.output_records
    print('Output of %s completed records to firehose.' % (str(len(output_records))))
    return {"records": output_records}
