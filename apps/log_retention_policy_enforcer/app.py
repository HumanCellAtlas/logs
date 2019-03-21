#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This AWS Lambda function allowed to delete the old Elasticsearch index
"""

import boto3
import json
import logging
import os

from dcplib.aws_secret import AwsSecret

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

config = json.loads(AwsSecret('logs/_/log_retention_policy_enforcer.json').value)

logs_client = boto3.client('logs')


class LogRetentionPolicyEnforcer:

    def __init__(self, client, ttls=dict(), prefix=None, default_days=1827):
        self.client = client
        self.ttls = ttls
        # users can set these by hand
        self.prefix = prefix
        self.default_days = default_days

    @staticmethod
    def from_ttl_file(client, filename):
        ttls = dict()
        with open(filename, 'r') as config_file:
            for line in config_file.read().splitlines()[1:]:
                log_group, days_str = line.split(',')
                ttls[log_group] = int(days_str)
        return LogRetentionPolicyEnforcer(client=client, ttls=ttls)

    def _describe_log_groups(self, next_token):
        if self.prefix is not None and next_token is not None:
            return self.client.describe_log_groups(logGroupNamePrefix=self.prefix, nextToken=next_token)
        elif self.prefix is not None:
            return self.client.describe_log_groups(logGroupNamePrefix=self.prefix)
        elif next_token is not None:
            return self.client.describe_log_groups(nextToken=next_token)
        else:
            return self.client.describe_log_groups()

    def _paginate_log_groups(self):
        response = self._describe_log_groups(None)
        while response is not None:
            for group in response['logGroups']:
                yield group['logGroupName'], group.get('retentionInDays')
            if 'nextToken' in response:
                response = self._describe_log_groups(response['nextToken'])
            else:
                response = None

    def run(self):
        for log_group_name, current_retention_in_days in self._paginate_log_groups():
            desired_retention_in_days = self.ttls.get(log_group_name, self.default_days)
            if current_retention_in_days == desired_retention_in_days:
                logger.info("Log group {} already has a retention policy of {} days".format(log_group_name, desired_retention_in_days))
            else:
                self.client.put_retention_policy(logGroupName=log_group_name, retentionInDays=desired_retention_in_days)
                logger.info("Set TTL for logs in log group {} to {} days".format(log_group_name, desired_retention_in_days))


def handler(event, context):
    """Main Lambda function
    """
    enforcer = LogRetentionPolicyEnforcer(logs_client, config['log_retention_ttls'])
    enforcer.run()
