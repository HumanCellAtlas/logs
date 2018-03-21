import unittest
import json
from io import BytesIO
import gzip
import base64
from lib.firehose_record_transmitter import FirehoseRecordTransmitter
from lib.firehose_record_processor import FirehoseRecordProcessor


class TestFirehoseRecordTransmitter(unittest.TestCase):
    region = "us-east-1"
    stream_name = "Kinesis-Firehose-ELK-staging"

    def test_chunk_records(self):
        records_to_transmit = list(range(0, 700))
        firehose_rec_transmitter = FirehoseRecordTransmitter(self.region, self.stream_name, records_to_transmit)
        firehose_rec_transmitter._chunk_records(100)
        self.assertEqual(len(firehose_rec_transmitter.record_chunks), 7)

    def test_transmit(self):
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
        data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}, {"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}]
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        input_records = [{"data": base64.b64encode(out.getvalue()), "recordId": "12345"}]
        firehose_record_processor = FirehoseRecordProcessor(input_records)
        firehose_record_processor.run()

        records_to_reingest = firehose_record_processor.records_to_reingest
        self.assertEqual(len(records_to_reingest), 2)
        firehose_rec_transmitter = FirehoseRecordTransmitter(self.region, self.stream_name, records_to_reingest)
        firehose_rec_transmitter.transmit()
