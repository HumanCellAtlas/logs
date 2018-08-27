import json
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
    alarm_name = alert_message['AlarmName']
    new_state = alert_message['NewStateValue']
    reason = alert_message['NewStateReason']

    alert_url = 'https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#alarm:alarmFilter=ANY;name={}'.format(
        alarm_name)
    slack_message = "<{alert_url}|{alarm_name}> state is now {new_state}: {reason}".format(
        alert_url=alert_url, alarm_name=alarm_name, new_state=new_state, reason=reason)
    post_message_to_url(slack_url, {"channel": slack_channel , "text": slack_message})


def get_secret():
    secret_name = "logs/_/cwl_to_slack.json"
    endpoint_url = "https://secretsmanager.us-east-1.amazonaws.com"
    region_name = "us-east-1"

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name,
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

