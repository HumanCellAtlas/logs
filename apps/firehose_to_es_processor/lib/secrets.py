import json
from dcplib.aws_secret import AwsSecret

config = json.loads(AwsSecret('logs/_/firehose_to_es_processor.json').value)
