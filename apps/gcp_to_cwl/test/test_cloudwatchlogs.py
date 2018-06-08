#!/usr/bin/env python
import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import unittest
import boto3
import uuid
from datetime import datetime
from contextlib import contextmanager
from cloudwatchlogs import CloudWatchLogs
from botocore.exceptions import ClientError
from test import eventually


class TestCloudWatchLogsClient(unittest.TestCase):

    @classmethod
    @contextmanager
    def test_context(cls):
        client = boto3.client('logs')
        test_log_group = f"test-log-group.{str(uuid.uuid4())}"
        test_log_stream = f"test-log-group.{str(uuid.uuid4())}"
        try:
            yield test_log_group, test_log_stream
        finally:
            try:
                client.delete_log_group(logGroupName=test_log_group)
            except ClientError as e:
                pass

    def test_prepare(self):
        with self.test_context() as (log_group, log_stream):
            cloudwatchlogs = CloudWatchLogs()
            token = cloudwatchlogs.prepare(log_group, log_stream)

            @eventually(5.0, 1.5)
            def test():
                result = cloudwatchlogs.client.describe_log_groups(
                    logGroupNamePrefix=log_group,
                    limit=2
                )
                self.assertEqual(
                    [ele['logGroupName'] for ele in result['logGroups']],
                    [log_group]
                )
                result = cloudwatchlogs.client.describe_log_streams(
                    logGroupName=log_group,
                    logStreamNamePrefix=log_stream,
                    limit=2
                )
                self.assertEqual(
                    [ele['logStreamName'] for ele in result['logStreams']],
                    [log_stream]
                )
                self.assertEqual(token, None)
            test()

    def test_put_log_events_valid_token(self):
        response = self._test_put(valid_token=True)
        self.assertNotEqual(None, response['nextSequenceToken'])
        self.assertEqual(200, response['ResponseMetadata']['HTTPStatusCode'])

    def test_put_log_events_invalid_token(self):
        response = self._test_put(valid_token=False)
        self.assertNotEqual(None, response['nextSequenceToken'])
        self.assertEqual(200, response['ResponseMetadata']['HTTPStatusCode'])

    def _test_put(self, valid_token):
        with self.test_context() as (log_group, log_stream):
            if valid_token:
                cache = dict()
            else:
                cache = {
                    f"{log_group}.{log_stream}": 'trash'
                }
            cloudwatchlogs = CloudWatchLogs()
            return cloudwatchlogs.put_log_events(
                request={
                    'logGroupName': log_group,
                    'logStreamName': log_stream,
                    'logEvents': [
                        {
                            'timestamp': int(datetime.utcnow().timestamp() * 1000),
                            'message': 'message',
                        }
                    ]
                },
                sequence_token_cache=cache,
            )


if __name__ == '__main__':
    unittest.main()
