#!/usr/bin/env python
import boto3
import os
import sys
import unittest
import uuid
from contextlib import contextmanager
from botocore.exceptions import ClientError

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from app import LogRetentionPolicyEnforcer


class TestCloudWatchLogsClient(unittest.TestCase):

    logs_client = boto3.client('logs')

    @classmethod
    @contextmanager
    def _test_context(cls):
        client = boto3.client('logs')
        test_log_group = f"test-log-group.{str(uuid.uuid4())}"
        cls.logs_client.create_log_group(logGroupName=test_log_group)
        try:
            yield test_log_group
        finally:
            try:
                client.delete_log_group(logGroupName=test_log_group)
            except ClientError as e:
                pass

    def test_paginate(self):
        with self._test_context() as test_log_group:
            enforcer = LogRetentionPolicyEnforcer(self.logs_client, prefix=test_log_group)

            self.assertEquals(
                list(enforcer._paginate_log_groups()),
                [(test_log_group, None)]
            )

    def test_run_default(self):
        with self._test_context() as test_log_group:
            enforcer = LogRetentionPolicyEnforcer(self.logs_client, prefix=test_log_group)
            enforcer.run()

            retention_in_days = TestCloudWatchLogsClient.logs_client.describe_log_groups(
                logGroupNamePrefix=test_log_group,
                limit=1
            )['logGroups'][0]['retentionInDays']

            self.assertEquals(retention_in_days, enforcer.default_days)

    def test_run_specified_ttl(self):
        with self._test_context() as test_log_group:
            enforcer = LogRetentionPolicyEnforcer(self.logs_client, prefix=test_log_group, ttls={test_log_group: 731})
            enforcer.run()

            retention_in_days = TestCloudWatchLogsClient.logs_client.describe_log_groups(
                logGroupNamePrefix=test_log_group,
                limit=1
            )['logGroups'][0]['retentionInDays']

            self.assertEquals(retention_in_days, 731)


if __name__ == '__main__':
    unittest.main()
