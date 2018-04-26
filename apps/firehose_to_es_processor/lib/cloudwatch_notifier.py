import boto3
from itertools import groupby
from operator import itemgetter
from collections import defaultdict

cloudwatch = boto3.client('cloudwatch')


def observe_counts(report):
    per_log_group_per_type_counts_metric_data = [
        {
            'MetricName': 'By Log Group, by Type',
            'Dimensions': [
                {
                    'Name': 'LogGroup',
                    'Value': log_group
                },
                {
                    'Name': 'CountType',
                    'Value': count_type
                },
            ],
            'Value': count,
            'Unit': 'Count',
            'StorageResolution': 60
        } for (log_group, count_type, count) in report
    ]
    for metric_data_chunk in _chunks(per_log_group_per_type_counts_metric_data, 20):
        cloudwatch.put_metric_data(
            MetricData=metric_data_chunk,
            Namespace='Logs',
        )

    per_type_counts = defaultdict(int)
    for (log_group, count_type, count) in report:
        per_type_counts[count_type] += count

    per_type_metric_data = [
        {
            'MetricName': 'By Type',
            'Dimensions': [
                {
                    'Name': 'CountType',
                    'Value': count_type
                }
            ],
            'Value': count,
            'Unit': 'Count',
            'StorageResolution': 60
        } for (count_type, count) in per_type_counts.items()
    ]
    for metric_data_chunk in _chunks(per_type_metric_data, 20):
        cloudwatch.put_metric_data(
            MetricData=metric_data_chunk,
            Namespace='Logs',
        )


def _chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]
