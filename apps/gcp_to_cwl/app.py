import logging
import os
import sys
import json
import typing

from datetime import timedelta
from datetime import datetime
from contextlib import contextmanager
from dateutil.parser import parse as dt_parse

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), './lib'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from cloudwatchlogs import CloudWatchLogs
from pubsub import SynchronousPullClient
from secrets import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handler(input, context):
    batch_size = 1000
    log_subscription = config['gcp_log_topic_subscription_name']

    batch_client = SynchronousPullClient(
        config['gcp_exporter_google_application_credentials']['project_id'],
        log_subscription)
    cloudwatchlogs = CloudWatchLogs()
    sequence_token_cache = {}

    total = 0
    for unformatted_log_entries in batch_client.to_generator(batch_size):
        num_log_entries = len(unformatted_log_entries)
        total += num_log_entries
        logger.info(json.dumps({'operation': 'batch_pull', 'num_unformatted_log_entries': num_log_entries}))
        requests, log_group_counts = group_entries_into_requests(unformatted_log_entries)
        logger.info(json.dumps({**{'operation': 'format_log_entries'}, **{'counts': log_group_counts}}))
        for request in requests:
            try:
                cloudwatchlogs.put_log_events(request, sequence_token_cache)
            except Exception as e:
                logger.info("ERROR on input: " + str(unformatted_log_entries))
                raise e
    logger.info('Processed {} entries in total.'.format(total))


@contextmanager
def file(filename, mode):
    f = open(filename, mode)
    try:
        yield f
    finally:
        f.close()


def group_entries_into_requests(unformatted_log_entries) -> (typing.List[dict], dict):
    twenty_three_hours_ago = (
        datetime.utcnow() - timedelta(hours=23)).timestamp() * 1000
    requests = {}
    log_group_counts = {}

    for unformatted_entry in unformatted_log_entries:
        log_entry = format_log_entry(unformatted_entry)
        log_group = get_log_group(unformatted_entry)

        if log_group not in requests:
            log_group_counts[log_group] = {'filtered': 0, 'unfiltered': 0}
            requests[log_group] = {
                'logGroupName': log_group,
                'logStreamName': 'default',
                'logEvents': []
            }

        log_group_counts[log_group]['unfiltered'] += 1

        if log_entry['timestamp'] > twenty_three_hours_ago and log_entry['message'] is not None:
            log_group_counts[log_group]['filtered'] += 1
            requests[log_group]['logEvents'].append(log_entry)

    for log_group, request in requests.items():
        request['logEvents'].sort(key=lambda r: r['timestamp'])

    return list(filter(lambda r: len(r['logEvents']) > 0, requests.values())), log_group_counts


def format_log_entry(unformatted_log_entry) -> dict:
    return {
        'timestamp': int(dt_parse(unformatted_log_entry['timestamp']).timestamp() * 1000),
        'message': get_log_message(unformatted_log_entry)
    }


def get_log_message(unformatted_log_entry):
    if 'textPayload' in unformatted_log_entry:
        return unformatted_log_entry['textPayload']
    elif 'jsonPayload' in unformatted_log_entry:
        return json.dumps(unformatted_log_entry['jsonPayload'])
    elif 'protoPayload' in unformatted_log_entry:
        return str(unformatted_log_entry['protoPayload'])


def get_log_group(unformatted_log_entry) -> str:
    resource_name_map = {
        'gcs_bucket': 'bucket_name',
        'cloud_function': 'function_name',
        'gae_app': 'module_id',
        'container': 'container_name',
    }
    project_id = unformatted_log_entry['resource']['labels']['project_id']
    resource_type = unformatted_log_entry['resource']['type']
    resource_name_key = resource_name_map.get(resource_type)
    resource_name_suffix = f"/{unformatted_log_entry['resource']['labels'][resource_name_key]}" \
        if resource_name_key else ''
    return f"/gcp/{project_id}/{resource_type}{resource_name_suffix}"
