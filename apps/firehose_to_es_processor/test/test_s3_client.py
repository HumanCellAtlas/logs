import json
import os
import sys
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from lib.s3_client import S3Client
from lib import firehose_records

from dcplib.aws_secret import AwsSecret

infra_config = json.loads(AwsSecret('logs/_/config.json').value)


class TestS3Client(unittest.TestCase):

    region = "us-east-1"
    account_id = infra_config['account_id']
    bucket = "logs-test-{0}".format(account_id)
    s3_client = S3Client(region, bucket)
    s3 = s3_client.s3

    def setUp(self):
        travis_build_id = os.environ.get('TRAVIS_BUILD_ID')
        self.s3_object_key = "test/data/Kinesis-Firehose-log-file-test"
        if travis_build_id:
            self.s3_object_key = self.s3_object_key + "-" + travis_build_id
        data = open("test/data/file.txt.gz", 'rb')
        try:
            self.s3.Bucket(self.bucket).put_object(Key=self.s3_object_key, Body=data)
        finally:
            data.close()

    def tearDown(self):
        self.s3_client.delete_file(self.s3_object_key)

    def test_s3_client(self):
        file = self.s3_client.retrieve_file(self.s3_object_key)['Body']
        input_records = self.s3_client.unzip_and_parse_firehose_s3_file(file)
        record_stream = firehose_records.from_docs(input_records)
        output_records = list(record_stream)
        self.assertEqual(len(output_records), 3)


if __name__ == '__main__':
    unittest.main()
