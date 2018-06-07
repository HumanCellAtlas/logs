import json
from dcplib.aws_secret import AwsSecret


config = json.loads(AwsSecret('logs/_/gcp_to_cwl.json').value)

_infra_config = json.loads(AwsSecret('logs/_/config.json').value)
config['gcp_log_topic_subscription_name'] = _infra_config['gcp_log_topic_subscription_name']
