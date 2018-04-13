from io import BytesIO
import gzip
import json
import base64
from datetime import datetime
from lib.util import extract_json
import os
from airbrake.notifier import Airbrake
import re

airbrake_flag = os.environ.get('AIRBRAKE_FLAG')
airbrake_notifier = None
if airbrake_flag and airbrake_flag == "True":
    airbrake_notifier = Airbrake(project_id=os.environ.get("AIRBRAKE_PROJECT_ID"), api_key=os.environ.get("AIRBRAKE_API_KEY"))
    print("Airbrake notifications are enabled")


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

        message = transformed_payload['@message']
        log_group = transformed_payload['@log_group']
        log_stream = self.record["logStream"]
        if airbrake_notifier and self._is_message_appropriate_for_airbrake(message, log_group):
            airbrake_error = "'{0} {1} '@log_stream': {2}".format(log_group, message, log_stream)
            try:
                airbrake_notifier.notify(str(airbrake_error))
            except:
                pass

        return transformed_payload

    def _is_message_appropriate_for_airbrake(self, message, log_group):
        send_to_airbrake = False

        blacklisted_log_group_names = os.environ.get("AIRBRAKE_BLACKLISTED_LOG_GROUP_NAMES")
        blacklisted_log_group_names_regex_string = "|".join(blacklisted_log_group_names.split())
        blacklisted_log_group_names_regexp = re.compile(blacklisted_log_group_names_regex_string, re.IGNORECASE)

        whitelisted_log_message_terms = os.environ.get("AIRBRAKE_WHITELISTED_LOG_MESSAGE_TERMS")
        whitelisted_log_message_terms_regex_string = "|".join(whitelisted_log_message_terms.split())
        whitelisted_log_message_terms_regexp = re.compile(whitelisted_log_message_terms_regex_string, re.IGNORECASE)

        if whitelisted_log_message_terms_regexp.search(message) and not blacklisted_log_group_names_regexp.search(log_group):
            send_to_airbrake = True
        return send_to_airbrake
