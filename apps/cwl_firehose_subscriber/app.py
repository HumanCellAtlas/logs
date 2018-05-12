import boto3
import re
import os

blacklisted_log_group_names = os.environ["BLACKLISTED_LOG_GROUPS"]


def is_log_group_name_blacklisted(log_group_name, blacklisted_names=blacklisted_log_group_names):
    blacklisted = False
    regex_string = "|".join(blacklisted_names.split())
    regexp = re.compile(regex_string, re.IGNORECASE)
    if regexp.search(log_group_name):
        blacklisted = True
    return blacklisted


def put_subscription_filter(log_group_name, destination_arn, role_arn):
    logs_client = boto3.client('logs')
    logs_client.put_subscription_filter(
        logGroupName=log_group_name,
        filterName="firehose",
        filterPattern='',
        destinationArn=destination_arn,
        roleArn=role_arn
    )


def handler(event, context):
    """Main Lambda function
    """
    logs_client = boto3.client('logs')
    log_group_name = event['detail']['requestParameters']['logGroupName']
    account_id = context.invoked_function_arn.split(":")[4]
    delivery_stream_arn = "arn:aws:firehose:us-east-1:{0}:deliverystream/Kinesis-Firehose-ELK".format(account_id)
    cwl_to_kinesis_role_arn = "arn:aws:iam::{0}:role/cwl-firehose".format(account_id)
    if not is_log_group_name_blacklisted(log_group_name):
        print("Subscribing log group {0} to firehose".format(log_group_name))
        put_subscription_filter(log_group_name, delivery_stream_arn, cwl_to_kinesis_role_arn)
    else:
        print("Log group {0} is blacklisted. Not subscribed to firehose".format(log_group_name))
