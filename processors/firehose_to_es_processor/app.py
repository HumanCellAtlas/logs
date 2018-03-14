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
3) Set the result to Dropped for any record whose messageType is not DATA_MESSAGE. Such records do not contain any log events.
4) For records whose messageType is DATA_MESSAGE, extract the individual log events from the logEvents field, and pass
   each one to the transform_log_event method. Individual parents with more than one children log records are transformed, encoded, and requeued for ingestion.
5) Transformed records are sent back to kinesis firehose ready for the final destination.
6) Any additional records which exceed 6MB will be re-ingested back into Firehose.

"""

import base64
import json
import gzip
from io import BytesIO
import boto3
from datetime import datetime


def json_bounds(data):
    """
        Returns indices for opening and closing brackets in incoming data string

        Args:
        data (string): Input log event data

        Returns
        (beginning_index, end_index)

    """
    beginning_index = None
    unclosed_brace_count = 0
    end_index = None

    for idx, char in enumerate(data):
        if char == "{":
            unclosed_brace_count += 1
            if beginning_index is None:
                beginning_index = idx
        elif beginning_index and char == "}":
            unclosed_brace_count -= 1
            if end_index is None and unclosed_brace_count == 0:
                end_index = idx
                break

    return beginning_index, end_index


def parse_json(data):
    """
        Returns extracted JSON if valid or None if not found or invalid from data string

        Args:
        data (string): Input log event data

        Output:
        dict
    """
    json_bound_loci = json_bounds(data)
    beginning_index = json_bound_loci[0]
    end_index = json_bound_loci[1]
    if beginning_index and end_index:
        try:
            formatted_data = data[beginning_index:end_index + 1]
            json_valid_data = formatted_data.replace("'", '"')
            formatted_data = json.loads(json_valid_data)
            return formatted_data
        except:
            return {}
    return {}


def transform_log_event(log_event, data):
    """Transform each log event.

    Args:
    log_event (dict): The original log event. Structure is {"id": str, "timestamp": long, "message": str}

    Returns:
    dict: transformed payload
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

    transformed_message = parse_json(log_event["message"])
    if transformed_message and type(transformed_message) == dict:
        transformed_payload["@message"] = json.dumps(transformed_message)
        for k, v in transformed_message.items():
            transformed_payload[k] = json.dumps(v)

    return transformed_payload


def parse_records(records, records_to_reingest):
    for rec in records:
        data = base64.b64decode(rec['data'])
        strio_data = BytesIO(data)
        try:
            with gzip.GzipFile(fileobj=strio_data, mode='r') as f:
                data = json.loads(f.read())
        except OSError:
            # likely the data was re-ingested into firehose
            pass

        recId = rec['recordId']
        # re-ingested data into firehose

        if type(data) == bytes:
            decoded = data.decode()
            yield {
                'data': decoded,
                'result': 'Ok',
                'recordId': recId
            }
        elif data['messageType'] != 'DATA_MESSAGE':
            yield {
                'result': 'Dropped',
                'recordId': recId
            }
        else:
            transformed_events = [transform_log_event(e, data) for e in data['logEvents']]
            if len(transformed_events) > 1:
                for event in transformed_events:
                    json_event = json.dumps(event)
                    data = base64.b64encode(json_event.encode()).decode()
                    records_to_reingest.append({
                        'Data': data
                    })
                yield {
                    'result': 'Dropped',
                    'recordId': recId
                }
            else:
                json_event = json.dumps(transformed_events[0])
                data = base64.b64encode(json_event.encode()).decode()
                yield {
                    'data': data,
                    'result': 'Ok',
                    'recordId': recId
                }


def chunk_put_records(stream_name, records, client, attempts_made, max_attempts, chunk_size=450):
    """Yield successive chunks from records."""
    for i in range(0, len(records), chunk_size):
        chunked_records = records[i:i + chunk_size]
        print('Reingesting %d records chunked' % (len(chunked_records)))
        put_record_chunk(stream_name, chunked_records, client, attempts_made, max_attempts)


def put_record_chunk(stream_name, records, client, attempts_made, max_attempts):
    """Put record chunk to delivery stream with built in retry"""
    failed_records = []
    try:
        response = client.put_record_batch(DeliveryStreamName=stream_name, Records=records)
    except Exception as e:
        failed_records = records

    # if there are no failed_records (put_record_batch succeeded), iterate over the response to gather ind failures
    if not failed_records and response['FailedPutCount'] > 0:
        for idx, res in enumerate(response['RequestResponses']):
            if res.get('ErrorCode'):
                failed_records.append(records[idx])

    if len(failed_records) > 0:
        if attempts_made + 1 < max_attempts:
            print('Some records failed while calling put_record_chunk, retrying')
            put_record_chunk(stream_name, failed_records, client, attempts_made + 1, max_attempts)
        else:
            raise RuntimeError('Could not put records after %s attempts.' % (str(max_attempts)))


def process_records(records, region, stream_name):
    """Wraps processing of records, monitoring bytes and records to reingest"""
    records_to_reingest = []
    records = list(parse_records(records, records_to_reingest))

    project_size = 0
    for idx, rec in enumerate(records):
        if rec['result'] == 'Dropped':
            continue
        project_size += len(rec['data']) + len(rec['recordId'])
        # Lambdas have limited output bytes
        if project_size > 4000000:
            records_to_reingest.append({
                'Data': rec['data']
            })
            records[idx]['result'] = 'Dropped'
            del(records[idx]['data'])

    if len(records_to_reingest) > 0:
        client = boto3.client('firehose', region_name=region)
        chunk_put_records(stream_name, records_to_reingest, client, attempts_made=0, max_attempts=20)
        print('Reingested %d records total' % (len(records_to_reingest)))
    else:
        print('No records to be reingested')

    print('%d records successfully processed for destination' % (len(records)))

    return {"records": records}


def handler(event, context):
    """Main function"""
    stream_arn = event['deliveryStreamArn']
    region = stream_arn.split(':')[3]
    stream_name = stream_arn.split('/')[1]
    input_records = event['records']
    output = process_records(input_records, region, stream_name)
    return output
