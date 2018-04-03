import unittest
from lib.firehose_record_processor import FirehoseRecordProcessor
import json
from io import BytesIO
import gzip
import base64


class TestFirehoseRecordProcessor(unittest.TestCase):

    def test_run_with_reingested_message_ready_for_es(self):
        data = {
            "@message": "test message",
            "@id": 123,
            "@owner": "test owner",
            "@log_group": "test log group",
            "@log_stream": "test log stream"
        }
        data = base64.b64encode(json.dumps(data).encode())
        input_list = [{"data": data, "recordId": "123"}]
        firehose_record_processor = FirehoseRecordProcessor(input_list)
        firehose_record_processor.run()

        output_records = firehose_record_processor.output_records
        self.assertEqual(len(firehose_record_processor.records_to_reingest), 0)
        self.assertEqual(len(output_records), 1)
        self.assertEqual(firehose_record_processor.output_records[0]['result'], 'Ok')
        self.assertEqual(output_records[0]["recordId"], "123")

        json_b64_decoded_data = json.loads(output_records[0]["data"])
        self.assertEqual(json_b64_decoded_data["@log_group"], "test log group")
        self.assertEqual(json_b64_decoded_data["@log_stream"], "test log stream")
        self.assertEqual(json_b64_decoded_data["@message"], "test message")
        self.assertEqual(json_b64_decoded_data["@owner"], "test owner")
        self.assertEqual(json_b64_decoded_data["@id"], 123)

    def test_run_with_message_for_dropping(self):
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'NOT DATA'}
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        input_records = [{"data": base64.b64encode(out.getvalue()), "recordId": "123"}]
        firehose_record_processor = FirehoseRecordProcessor(input_records)
        firehose_record_processor.run()
        self.assertEqual(firehose_record_processor.output_records[0]['result'], 'Dropped')

    def test_run_with_one_untransformed_log_event_in_record(self):
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
        data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}]
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        input_records = [{"data": base64.b64encode(out.getvalue()), "recordId": "12345"}]
        firehose_record_processor = FirehoseRecordProcessor(input_records)
        firehose_record_processor.run()
        output_records = firehose_record_processor.output_records
        self.assertEqual(output_records[0]['result'], 'Dropped')
        self.assertEqual(output_records[0]["recordId"], "12345")

    def test_run_with_multiple_untransformed_log_events_in_record(self):
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
        data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}, {"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}]
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        input_records = [{"data": base64.b64encode(out.getvalue()), "recordId": "12345"}]
        firehose_record_processor = FirehoseRecordProcessor(input_records)
        firehose_record_processor.run()

        output_records = firehose_record_processor.output_records
        self.assertEqual(output_records[0]['result'], 'Dropped')
        self.assertEqual(output_records[0]["recordId"], "12345")
        self.assertEqual(output_records[0].get('data'), None)

    def test_pare_down_records_for_max_output(self):
        message = "test message"*200000
        data = {
            "@message": message,
            "@id": 123,
            "@owner": "test owner",
            "@log_group": "test log group",
            "@log_stream": "test log stream"
        }
        data = base64.b64encode(json.dumps(data).encode())
        input_list = [{"data": data, "recordId": "123"}, {"data": data, "recordId": "124"}]
        firehose_record_processor = FirehoseRecordProcessor(input_list)
        firehose_record_processor.run()
        records_to_reingest = firehose_record_processor.records_to_reingest
        output_records = firehose_record_processor.output_records
        self.assertEqual(len(records_to_reingest), 1)
        self.assertEqual(len(output_records), 2)
        self.assertEqual(output_records[0]['result'], 'Ok')
        self.assertNotEqual(output_records[0].get('data'), None)
        self.assertEqual(output_records[1]['result'], 'Dropped')
        self.assertEqual(output_records[1].get('data'), None)
