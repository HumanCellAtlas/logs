import unittest
import app
import boto3
import os
import uuid


class TestApp(unittest.TestCase):

    def test_is_log_group_name_blacklisted(self):
        test_blacklisted_log_groups = "test blue"

        # should return true for log group containing same case blacklisted value
        test_log_group_1 = "green-test"
        blacklisted = app.is_log_group_name_blacklisted(test_log_group_1, test_blacklisted_log_groups)
        self.assertEqual(blacklisted, True)

        # should return true for log group containing different case blacklisted value
        test_log_group_2 = "green-TEST"
        blacklisted = app.is_log_group_name_blacklisted(test_log_group_2, test_blacklisted_log_groups)
        self.assertEqual(blacklisted, True)

        # should return false for log group not containing blacklisted value
        test_log_group_2 = "blu-TES"
        blacklisted = app.is_log_group_name_blacklisted(test_log_group_2)
        self.assertEqual(blacklisted, False)

        # should return true for log group containing blacklisted value
        test_log_group_3 = "subscribertest"
        blacklisted = app.is_log_group_name_blacklisted(test_log_group_3)
        self.assertEqual(blacklisted, True)

         # should return true for log group containing blacklisted value
        test_log_group_3 = "/aws/lambda/Firehose-CWL-Processor"
        blacklisted = app.is_log_group_name_blacklisted(test_log_group_3)
        self.assertEqual(blacklisted, True)

        # should return true for log group containing blacklisted value
        test_log_group_3 = "/aws/lambda/test_log_group-12345"
        blacklisted = app.is_log_group_name_blacklisted(test_log_group_3)
        self.assertEqual(blacklisted, True)

    def test_subscription_filter(self):
        logs_client = boto3.client('logs')
        log_group_name = f"/aws/lambda/test_log_group-{uuid.uuid4()}"
        try:
            # create test log group
            logs_client = boto3.client('logs')
            logs_client.create_log_group(logGroupName=log_group_name)

            # put subscription filter to kinesis on log group
            account_id = os.environ["ACCOUNT_ID"]
            delivery_stream_arn = "arn:aws:firehose:us-east-1:{0}:deliverystream/Kinesis-Firehose-ELK".format(account_id)
            cwl_to_kinesis_role_arn = "arn:aws:iam::{0}:role/cwl-firehose".format(account_id)
            app.put_subscription_filter(log_group_name, delivery_stream_arn, cwl_to_kinesis_role_arn)

            # fetch subscription filter and check / assert
            filters = logs_client.describe_subscription_filters(logGroupName=log_group_name)
            filter_name = filters['subscriptionFilters'][0]['filterName']
            self.assertEqual(filter_name, 'firehose')

        finally:
            logs_client.delete_log_group(logGroupName=log_group_name)
