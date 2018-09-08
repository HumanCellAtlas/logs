import json
import os

import requests
import boto3
from botocore.exceptions import ClientError


def handler(event, context):
    """
    Post alert to slack webhook
    """
    alert_message = json.loads(event['Records'][0]['Sns']['Message'])
    alarm_name = alert_message['AlarmName']
    reason = alert_message['NewStateReason']
    new_state = alert_message['NewStateValue']
    color = "good" if new_state == 'OK' else "danger"

    region = os.getenv('AWS_DEFAULT_REGION')
    alert_url = f'https://console.aws.amazon.com/cloudwatch/home?region={region}#alarm:alarmFilter=ANY;name={alarm_name}'
    link = f"<{alert_url}|{alarm_name}>"

    secrets = json.loads(get_secret()['SecretString'])
    default_slack_channel = secrets['slack_alert_channel']
    alarm_description = json.loads(alert_message['AlarmDescription'])
    slack_channel = alarm_description.get("slack_channel", default_slack_channel)
    description = alarm_description.get("description")
    slack_message = '\n'.join(
        [f"New state: {new_state}", f"Description: {description}", reason]
    )

    attachments = [{
        "fallback": f"{link} {slack_message}",
        "title": alarm_name,
        "title_link": alert_url,
        "text": slack_message,
        "color": color
    }]

    slack_url = secrets['slack_webhooks'][slack_channel]

    post_message_to_url(slack_url, {"attachments": attachments})


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
