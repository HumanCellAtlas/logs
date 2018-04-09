from io import BytesIO
import gzip
import json
import base64
from datetime import datetime
from lib.util import extract_json


class FirehoseRecord():

    def __init__(self, record):
        self.record = record
        self.message_type = record['messageType']

    def transform_and_extract_from_log_events_in_record(self):
        self.transformed_log_events = [self._transform_and_extract_from_log_event(event) for event in self.record['logEvents']]

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
            "@owner": self.record["owner"],
            "@log_group": self.record["logGroup"],
            "@log_stream": self.record["logStream"]
        }

        transformed_message = extract_json(log_event["message"])
        if transformed_message and type(transformed_message) == dict:
            for k, v in transformed_message.items():
                transformed_payload[k] = json.dumps(v)

        return transformed_payload
