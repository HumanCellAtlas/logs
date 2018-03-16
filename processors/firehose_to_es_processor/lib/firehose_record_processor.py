import json
import base64
from lib.firehose_record import FirehoseRecord


class FirehoseRecordProcessor():

    def __init__(self, input_records):
        self.input_records = input_records
        self.output_records = []
        self.records_to_reingest = []

    def run(self):
        for rec in self.input_records:

            record = FirehoseRecord(rec)
            record.decode_and_unzip()

            if type(record.data) == bytes and record.message_type is None:
                # Likely on its second round from firehose, ready for elastic search
                self._mark_record_ready_for_elastic_search(record)
            elif record.message_type != 'DATA_MESSAGE':
                # Not worthy of passing along as there is no data, mark for dropping
                self._mark_record_for_dropping(record)
            else:
                # Normal record with one or multiple untransformed cloudwatch log events
                record.transform_and_extract_from_log_events_in_record()
                if len(record.transformed_log_events) == 1:
                    json_event = json.dumps(record.transformed_log_events[0])
                    record.data = base64.b64encode(json_event.encode())
                    self._mark_record_ready_for_elastic_search(record)
                else:
                    self._mark_record_for_reingestion(record)

        self._pare_down_records_for_max_output()

    def _pare_down_records_for_max_output(self):

        byte_size = 0
        for idx, rec in enumerate(self.output_records):
            if rec['result'] == 'Dropped':
                continue
            byte_size += len(rec['data']) + len(rec['recordId'])

            # Lambdas have limited output bytes
            if byte_size > 4000000:
                self.records_to_reingest.append({
                    'Data': rec['data']
                })
                self.output_records[idx]['result'] = 'Dropped'
                del(self.output_records[idx]['data'])

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
        for event in record.transformed_log_events:
            json_event = json.dumps(event)
            data = base64.b64encode(json_event.encode()).decode()
            self.records_to_reingest.append({
                'Data': data
            })
        output = {
            'result': 'Dropped',
            'recordId': record.id
        }
        self.output_records.append(output)
