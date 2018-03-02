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

The code below will:

1) Gunzip the data
2) Parse the json
3) Set the result to ProcessingFailed for any record whose messageType is not DATA_MESSAGE, thus redirecting them to the
   processing error output. Such records do not contain any log events. You can modify the code to set the result to
   Dropped instead to get rid of these records completely.
4) For records whose messageType is DATA_MESSAGE, extract the individual log events from the logEvents field, and pass
   each one to the transformLogEvent method. You can modify the transformLogEvent method to perform custom
   transformations on the log events.
5) Concatenate the result from (4) together and set the result as the data of the record returned to Firehose. Note that
   this step will not add any delimiters. Delimiters should be appended by the logic within the transformLogEvent
   method.
6) Any additional records which exceed 6MB will be re-ingested back into Firehose.

"""

import base64
import json
import gzip
import StringIO
import boto3
from datetime import datetime


def transformLogEvent(log_event, data):
    """Transform each log event.

    The default implementation below just extracts the message and appends a newline to it.

    Args:
    log_event (dict): The original log event. Structure is {"id": str, "timestamp": long, "message": str}

    Returns:
    {"message": str, "id": str, "timestamp": str}
    """
    timestamp_in_seconds = log_event["timestamp"] / 1000.0
    transformed_timestamp = datetime.fromtimestamp(timestamp_in_seconds).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    transformed_payload = {
        "@message": log_event["message"],
        "@id": log_event["id"],
        "@timestamp": transformed_timestamp,
        "@owner": data["owner"],
        "@log_group": data["logGroup"],
        "@log_stream": data["logStream"]
    }
    return transformed_payload


def processRecords(records, records_to_reingest):
    for r in records:
        data = base64.b64decode(r['data'])
        striodata = StringIO.StringIO(data)
        try:
            with gzip.GzipFile(fileobj=striodata, mode='r') as f:
                data = json.loads(f.read())
        except IOError:
            # likely the data was re-ingested into firehose
            pass

        recId = r['recordId']
        # re-ingested data into firehose
        if type(data) == str:
            yield {
                'data': data,
                'result': 'Ok',
                'recordId': recId
            }
        elif data['messageType'] != 'DATA_MESSAGE':
            yield {
                'result': 'ProcessingFailed',
                'recordId': recId
            }
        else:
            transformed_events = [transformLogEvent(e, data) for e in data['logEvents']]
            if len(transformed_events) > 1:
                for event in transformed_events:
                    json_event = json.dumps(event)
                    data = base64.b64encode(buffer(json_event))
                    records_to_reingest.append({
                        'Data': data
                    })
                yield {
                    'result': 'Dropped',
                    'recordId': recId
                }
            else:
                json_event = json.dumps(transformed_events[0])
                data = base64.b64encode(buffer(json_event))
                yield {
                    'data': data,
                    'result': 'Ok',
                    'recordId': recId
                }


def chunk_put_records(streamName, records, client, attemptsMade, maxAttempts):
    """Yield successive chunks from records."""
    # remove hardcoded 450 into higher level variable
    for i in xrange(0, len(records), 450):
        chunked_records = records[i:i + 450]
        print('Reingesting %d records chunked' % (len(chunked_records)))
        put_record_chunk(streamName, chunked_records, client, attemptsMade, maxAttempts)


def put_record_chunk(streamName, records, client, attemptsMade, maxAttempts):
    failedRecords = []
    codes = []
    errMsg = ''
    try:
        response = client.put_record_batch(DeliveryStreamName=streamName, Records=records)
    except Exception as e:
        failedRecords = records
        errMsg = str(e)

    # if there are no failedRecords (put_record_batch succeeded), iterate over the response to gather results
    if not failedRecords and response['FailedPutCount'] > 0:
        for idx, res in enumerate(response['RequestResponses']):
            if not res['ErrorCode']:
                continue

            codes.append(res['ErrorCode'])
            failedRecords.append(records[idx])

        errMsg = 'Individual error codes: ' + ','.join(codes)

    if len(failedRecords) > 0:
        if attemptsMade + 1 < maxAttempts:
            print('Some records failed while calling put_record_chunk, retrying. %s' % (errMsg))
            put_record_chunk(streamName, failedRecords, client, attemptsMade + 1, maxAttempts)
        else:
            raise RuntimeError('Could not put records after %s attempts. %s' % (str(maxAttempts), errMsg))


def handler(event, context):
    streamARN = event['deliveryStreamArn']
    region = streamARN.split(':')[3]
    streamName = streamARN.split('/')[1]

    records_to_reingest = []
    records = list(processRecords(event['records'], records_to_reingest))
    projectedSize = 0
    for idx, rec in enumerate(records):
        if rec['result'] == 'ProcessingFailed' or rec['result'] == 'Dropped':
            continue
        projectedSize += len(rec['data']) + len(rec['recordId'])
        # 4000000 instead of 6291456 to leave ample headroom for the stuff we didn't account for
        if projectedSize > 4000000:
            records_to_reingest.append({
                'Data': rec['data']
            })
            records[idx]['result'] = 'Dropped'
            del(records[idx]['data'])

    if len(records_to_reingest) > 0:
        client = boto3.client('firehose', region_name=region)
        chunk_put_records(streamName, records_to_reingest, client, attemptsMade=0, maxAttempts=20)
        print('Reingested %d records total' % (len(records_to_reingest)))
    else:
        print('No records to be reingested')

    print('records length')
    print(len(records))

    return {"records": records}
