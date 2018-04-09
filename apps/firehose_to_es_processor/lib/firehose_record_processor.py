import json
from lib.firehose_record import FirehoseRecord


class FirehoseRecordProcessor():

    def __init__(self, input_records):
        self.input_records = input_records
        self.output_records = []

    def run(self):
        for rec in self.input_records:

            record = FirehoseRecord(rec)
            if record.message_type == 'DATA_MESSAGE':
                record.transform_and_extract_from_log_events_in_record()
                self.output_records += record.transformed_log_events
