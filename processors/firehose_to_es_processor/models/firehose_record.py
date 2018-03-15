from io import BytesIO
import gzip
import json
import base64
from datetime import datetime
from lib.util import extract_json


class FirehoseRecord():

    def __init__(self, record):
        self.id = record['recordId']
        self.data = record["data"]
        self.message_type = None

    def decode_and_unzip(self):
        decoded_data = base64.b64decode(self.data)
        strio_data = BytesIO(decoded_data)
        try:
            with gzip.GzipFile(fileobj=strio_data, mode='r') as f:
                self.json_data = json.loads(f.read())
                self.message_type = self.json_data['messageType']
        except OSError:
            # likely the data was re-ingested into firehose
            pass

    def transform_and_extract_from_log_events_in_record(self):
        self.transformed_log_events = [self._transform_and_extract_from_log_event(event) for event in self.json_data['logEvents']]

    def _transform_and_extract_from_log_event(self, log_event):
        """Transform each log event.

        Args:
        log_event (dict): The original log event. Structure is {"id": str, "timestamp": long, "message": str}

        Returns:
        dict: transformed payload
        """
        timestamp_in_seconds = log_event["timestamp"] / 1000.0
        transformed_timestamp = datetime.fromtimestamp(timestamp_in_seconds).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        transformed_payload = {
            "@message": log_event["message"],
            "@id": log_event["id"],
            "@timestamp": transformed_timestamp,
            "@owner": self.json_data["owner"],
            "@log_group": self.json_data["logGroup"],
            "@log_stream": self.json_data["logStream"]
        }

        transformed_message = extract_json(log_event["message"])
        if transformed_message and type(transformed_message) == dict:
            for k, v in transformed_message.items():
                transformed_payload[k] = json.dumps(v)

        return transformed_payload
