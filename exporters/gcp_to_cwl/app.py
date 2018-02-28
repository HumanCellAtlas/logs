import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), 'domovoilib'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import json
import typing
import domovoi
from cloudwatchlogs import CloudWatchLogs
from pubsub import SynchronousPullClient
from datetime import timedelta
from datetime import datetime
from contextlib import contextmanager
from dateutil.parser import parse as dt_parse


app = domovoi.Domovoi()


@app.scheduled_function("rate(2 minutes)")
def handler(input, context):
    batch_size = 2500
    log_subscription = os.environ['LOG_TOPIC_SUBSCRIPTION_NAME']

    with file(os.environ['GOOGLE_APPLICATION_CREDENTIALS'], 'r') as f:
        credentials = json.load(f)
    project_id = credentials['project_id']

    batch_client = SynchronousPullClient(project_id, log_subscription)
    cloudwatchlogs = CloudWatchLogs()
    sequence_token_cache = {}

    for unformatted_log_entries in batch_client.to_generator(batch_size):
        requests = group_entries_into_requests(unformatted_log_entries)
        for request in requests:
            try:
                cloudwatchlogs.put_log_events(request, sequence_token_cache)
            except Exception as e:
                print("ERROR on input: " + str(unformatted_log_entries))
                raise e


@contextmanager
def file(filename, mode):
    f = open(filename, mode)
    try:
        yield f
    finally:
        f.close()


def group_entries_into_requests(unformatted_log_entries) -> typing.List[dict]:
    twenty_three_hours_ago = (
        datetime.utcnow() - timedelta(hours=23)).timestamp() * 1000
    requests = {}

    for unformatted_entry in unformatted_log_entries:
        log_entry = format_log_entry(unformatted_entry)
        log_group = get_log_group(unformatted_entry)

        if log_group not in requests:
            requests[log_group] = {
                'logGroupName': log_group,
                'logStreamName': 'default',
                'logEvents': []
            }

        if log_entry['timestamp'] > twenty_three_hours_ago and log_entry['message'] is not None:
            requests[log_group]['logEvents'].append(log_entry)

    for log_group, request in requests.items():
        request['logEvents'].sort(key=lambda r: r['timestamp'])

    return list(filter(lambda r: len(r['logEvents']) > 0, requests.values()))


def format_log_entry(unformatted_log_entry) -> dict:
    return {
        'timestamp': int(dt_parse(unformatted_log_entry['timestamp']).timestamp() * 1000),
        'message': unformatted_log_entry['textPayload'] if 'textPayload' in unformatted_log_entry else unformatted_log_entry.get('protoPayload')
    }


def get_log_group(unformatted_log_entry) -> str:
    resource_name_map = {
        'gcs_bucket': 'bucket_name',
        'cloud_function': 'function_name',
        'gae_app': 'module_id',
    }
    project_id = unformatted_log_entry['resource']['labels']['project_id']
    resource_type = unformatted_log_entry['resource']['type']
    resource_name_key = resource_name_map.get(resource_type)
    resource_name_suffix = f"/{unformatted_log_entry['resource']['labels'][resource_name_key]}" \
        if resource_name_key else ''
    return f"/gcp/{project_id}/{resource_type}{resource_name_suffix}"
