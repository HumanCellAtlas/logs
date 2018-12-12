import boto3
import gzip
import io
from retrying import retry
from .json_object_stream import JsonObjectStream


class S3Client:
    def __init__(self, region, bucket):
        self.region = region
        self.bucket = bucket
        self.s3 = boto3.resource('s3')

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def retrieve_file(self, s3_object_key):
        obj = self.s3.Object(self.bucket, s3_object_key)
        return obj.get()

    @classmethod
    def unzip_and_parse_firehose_s3_file(cls, file):
        with gzip.GzipFile(fileobj=file, mode='r') as fh:
            fw = io.TextIOWrapper(fh, 'utf-8')
            fw._CHUNK_SIZE = 1
            os = JsonObjectStream(fw)
            for obj in iter(lambda: os.next(), None):
                yield obj

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def delete_file(self, s3_object_key):
        obj = self.s3.Object(self.bucket, s3_object_key)
        obj.delete()
