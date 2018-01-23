import base64
import gzip
import json
import os
import uuid
from contextlib import contextmanager


def decode(data) -> dict:
    return json.loads(base64.b64encode(data))


@contextmanager
def gcp_credentials():
    encoded_credentials_string = os.environ['GCLOUD_CREDENTIALS']
    credentials_file = f"/tmp/{uuid.uuid4()}.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file
    try:
        credentials_string = gzip.decompress(base64.b64decode(encoded_credentials_string))
        file = open(credentials_file, 'w')
        file.write(credentials_string)
        file.close()
        yield
    finally:
        os.remove(credentials_file)
