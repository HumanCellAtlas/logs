import json
import base64
import os
import re
import airbrake
from lib.firehose_record import FirehoseRecord

if os.environ.get('AIRBRAKE_FLAG'):
    logger = airbrake.getLogger(api_key=os.environ.get("AIRBRAKE_API_KEY"), project_id=os.environ.get("AIRBRAKE_PROJECT_ID"))


class FirehoseRecordProcessor():

    def __init__(self, input_records):
        self.input_records = input_records
        self.output_records = []
        self.records_to_reingest = []
        self.output_byte_size = 0

    def run(self):
        for rec in self.input_records:

            record = FirehoseRecord(rec)
            record.decode_and_unzip()

            if type(record.data) == bytes and record.message_type is None:
                # Likely on its second round from firehose, ready for elastic search
                if self._is_record_crossing_max_output_size_threshold(record):
                    self._mark_record_for_reingestion_and_airbrake(record)
                else:
                    self._mark_record_ready_for_elastic_search(record)
            elif record.message_type != 'DATA_MESSAGE':
                # Not worthy of passing along as there is no data, mark for dropping
                self._mark_record_for_dropping(record)
            else:
                # Normal record with one or multiple untransformed cloudwatch log events
                record.transform_and_extract_from_log_events_in_record()
                self._mark_record_for_reingestion_and_airbrake(record)

    def _is_record_crossing_max_output_size_threshold(self, record):
        self.output_byte_size += len(record.data) + len(record.id)

        # Lambdas have limited output bytes
        if self.output_byte_size > 4000000:
            return True
        else:
            return False

    def _mark_record_ready_for_elastic_search(self, record):
        output = {
            'data': record.data.decode(),
            'result': 'Ok',
            'recordId': record.id
        }
        self.output_records.append(output)

    def _mark_record_for_dropping(self, record):
        output = {
            'result': 'Dropped',
            'recordId': record.id
        }
        self.output_records.append(output)

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

    def _mark_record_for_reingestion_and_airbrake(self, record):
        if record.transformed_log_events:
            for event in record.transformed_log_events:
                json_event = json.dumps(event)
                data = base64.b64encode(json_event.encode()).decode()
                self.records_to_reingest.append({
                    'Data': data
                })
                message = event['@message']
                log_group = event['@log_group']
                airbrake_flag = os.environ.get('AIRBRAKE_FLAG')
                if airbrake_flag and airbrake_flag == "True" and self._is_message_appropriate_for_airbrake(message, log_group):
                    logger.exception(message)
        else:
            self.records_to_reingest.append({
                'Data': record.data.decode()
            })
        output = {
            'result': 'Dropped',
            'recordId': record.id
        }
        self.output_records.append(output)
