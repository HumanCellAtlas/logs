import boto3
import gzip
import json
import re
from retrying import retry


class S3Client():
    def __init__(self, region, bucket):
        self.region = region
        self.bucket = bucket
        self.s3 = boto3.resource('s3')

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def retrieve_file(self, s3_object_key):
        obj = self.s3.Object(self.bucket, s3_object_key)
        return obj.get()

    def unzip_and_parse_firehose_s3_file(self, file):
        json_events = []
        with gzip.GzipFile(fileobj=file['Body'], mode='r') as f:
            log_events = f.read().decode()
            to_split_on = '{"messageType":'
            split_events = [to_split_on + x for x in re.split(to_split_on, log_events)[1:]]
            for event in split_events:
                json_events.append(json.loads(event))
        return json_events

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def delete_file(self, s3_object_key):
        obj = self.s3.Object(self.bucket, s3_object_key)
        obj.delete()
