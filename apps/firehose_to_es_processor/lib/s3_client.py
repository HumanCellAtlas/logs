import boto3
import io
from retrying import retry
from .gzip_stream_reader import GzipStreamReader
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
        try:
            br = GzipStreamReader.from_file(file)
            fw = io.TextIOWrapper(br, 'utf-8')
            fw._CHUNK_SIZE = 1
            os = JsonObjectStream(fw)
            for obj in iter(lambda: os.next(), None):
                yield obj
        finally:
            file.close()

    @retry(wait_fixed=1000, stop_max_attempt_number=3)
    def delete_file(self, s3_object_key):
        obj = self.s3.Object(self.bucket, s3_object_key)
        obj.delete()
