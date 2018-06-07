import boto3
import json
import os
import unittest
import uuid

import app
from app import PrefixSet
from dcplib.aws_secret import AwsSecret

infra_config = json.loads(AwsSecret(name='logs/_/config.json').value)


class TestApp(unittest.TestCase):

    def test_prefix_set(self):
        blacklisted_log_groups = PrefixSet(["test", "blue"])

        # should return true for log group containing same case blacklisted value
        matches = blacklisted_log_groups.matches("green-test")
        self.assertEqual(matches, False)

        # should return true for log group containing different case blacklisted value
        matches = blacklisted_log_groups.matches("GREEN-TEST")
        self.assertEqual(matches, False)

        # should not match a matching string, but not in prefix position
        matches = blacklisted_log_groups.matches("something-blue")
        self.assertEqual(matches, False)

    def test_app_prefix_set(self):
        # should return true for log group containing blacklisted value
        blacklisted = app.blacklisted_log_groups.matches("subscribertest")
        self.assertEqual(blacklisted, True)

        # should return true for log group containing blacklisted value
        blacklisted = app.blacklisted_log_groups.matches("/aws/lambda/Firehose-CWL-Processor")
        self.assertEqual(blacklisted, True)

        # should return true for log group containing blacklisted value
        blacklisted = app.blacklisted_log_groups.matches("/aws/lambda/test_log_group-12345")
        self.assertEqual(blacklisted, True)

    def test_subscription_filter(self):
        logs_client = boto3.client('logs')
        log_group_name = f"/aws/lambda/test_log_group-{uuid.uuid4()}"
        try:
            # create test log group
            logs_client = boto3.client('logs')
            logs_client.create_log_group(logGroupName=log_group_name)

            # put subscription filter to kinesis on log group
            account_id = infra_config['account_id']
            delivery_stream_arn = "arn:aws:firehose:us-east-1:{0}:deliverystream/Kinesis-Firehose-ELK".format(account_id)
            cwl_to_kinesis_role_arn = "arn:aws:iam::{0}:role/cwl-firehose".format(account_id)
            app.put_subscription_filter(log_group_name, delivery_stream_arn, cwl_to_kinesis_role_arn)

            # fetch subscription filter and check / assert
            filters = logs_client.describe_subscription_filters(logGroupName=log_group_name)
            filter_name = filters['subscriptionFilters'][0]['filterName']
            self.assertEqual(filter_name, 'firehose')

            # it should not fail if the log group does not exist
            app.put_subscription_filter('fake-' + str(uuid.uuid4()), delivery_stream_arn, cwl_to_kinesis_role_arn)

        finally:
            logs_client.delete_log_group(logGroupName=log_group_name)
