#!/usr/bin/env python
"""
This script does an external update of firehose with a processing configuration pointing to a lambda function.

"""

import json
import sys
import boto3
import os

firehose_client = boto3.client('firehose')
lambda_client = boto3.client('lambda')

def handler(**args):
    '''
        This function updates the firehose with a processing configuration, since terraform does not currently support this option.
        Input:
            arguments: dict
        Output:
            dict
    '''
    delivery_stream_name = arguments["delivery_stream_name"]
    delivery_stream = firehose_client.describe_delivery_stream(DeliveryStreamName=delivery_stream_name)
    delivery_stream_desc = delivery_stream["DeliveryStreamDescription"]
    delivery_stream_version_id = delivery_stream_desc["VersionId"]
    destination = delivery_stream_desc["Destinations"][0]
    destination_id = destination["DestinationId"]

    lambda_function_name = arguments["lambda_name"]
    processing_lambda_func = lambda_client.get_function(FunctionName=lambda_function_name)
    processing_lambda_func_arn = processing_lambda_func["Configuration"]["FunctionArn"]
    processing_lambda_role_arn = "arn:aws:iam::{0}:role/kinesis-firehose-es-staging".format(os.environ["ACCOUNT_ID"])

    elastic_search_destination_update = {
        'ProcessingConfiguration': {
            'Enabled': True,
            'Processors': [
                {
                    'Type': 'Lambda',
                    'Parameters': [
                        {
                            'ParameterName': 'LambdaArn',
                            'ParameterValue': processing_lambda_func_arn
                        },
                        {
                            'ParameterName': 'NumberOfRetries',
                            'ParameterValue': '3'
                        },
                        {
                            'ParameterName': 'RoleArn',
                            'ParameterValue': processing_lambda_role_arn
                        },
                        {
                            'ParameterName': 'BufferSizeInMBs',
                            'ParameterValue': '1'
                        },
                        {
                            'ParameterName': 'BufferIntervalInSeconds',
                            'ParameterValue': '60'
                        }
                    ]
                },
            ]
        },
    }
    firehose_client.update_destination(
        DeliveryStreamName=delivery_stream_name,
        CurrentDeliveryStreamVersionId=delivery_stream_version_id,
        DestinationId=destination_id,
        ElasticsearchDestinationUpdate=elastic_search_destination_update)
    json.dump({"status": "successful"}, sys.stdout)



if __name__ == '__main__':
    args = json.load(sys.stdin)
    handler(args)
