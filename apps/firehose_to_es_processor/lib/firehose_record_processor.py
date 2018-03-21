import json
import base64
from lib.firehose_record import FirehoseRecord


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
                    self._mark_record_for_reingestion(record)
                else:
                    self._mark_record_ready_for_elastic_search(record)
            elif record.message_type != 'DATA_MESSAGE':
                # Not worthy of passing along as there is no data, mark for dropping
                self._mark_record_for_dropping(record)
            else:
                # Normal record with one or multiple untransformed cloudwatch log events
                record.transform_and_extract_from_log_events_in_record()
                self._mark_record_for_reingestion(record)

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

    def _mark_record_for_reingestion(self, record):
        if record.transformed_log_events:
            for event in record.transformed_log_events:
                json_event = json.dumps(event)
                data = base64.b64encode(json_event.encode()).decode()
                self.records_to_reingest.append({
                    'Data': data
                })
        else:
            self.records_to_reingest.append({
                'Data': record.data.decode()
            })
        output = {
            'result': 'Dropped',
            'recordId': record.id
        }
        self.output_records.append(output)
