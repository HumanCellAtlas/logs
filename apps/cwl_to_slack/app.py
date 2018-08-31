import json
import os

import requests
import boto3
from botocore.exceptions import ClientError


def handler(event, context):
    """
    main lambda function
    """

    secrets = json.loads(get_secret()['SecretString'])
    slack_url = secrets['slack_webhook_url']
    slack_channel = secrets['slack_alert_channel']

    alert_message = json.loads(event['Records'][0]['Sns']['Message'])
    print(alert_message)
    alarm_name = alert_message['AlarmName']
    new_state = alert_message['NewStateValue']
    reason = alert_message['NewStateReason']
    region = os.getenv('AWS_DEFAULT_REGION')

    alert_url = f'https://console.aws.amazon.com/cloudwatch/home?region={region}#alarm:alarmFilter=ANY;name={alarm_name}'
    slack_message = f"<{alert_url}|{alarm_name}> state is now {new_state}: {reason}"
    post_message_to_url(slack_url, {"channel": slack_channel , "text": slack_message})


def get_secret():
    secret_name = "logs/_/cwl_to_slack.json"

    region = os.getenv('AWS_DEFAULT_REGION')
    endpoint_url = f"https://secretsmanager.{region}.amazonaws.com"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region,
        endpoint_url=endpoint_url
    )

    try:
        secret_value = client.get_secret_value(
            SecretId=secret_name
        )
        return secret_value

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", e)


def post_message_to_url(url, message):
    body = json.dumps(message)
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)

