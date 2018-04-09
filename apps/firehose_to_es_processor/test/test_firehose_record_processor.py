import unittest
from lib.firehose_record_processor import FirehoseRecordProcessor
import json
from io import BytesIO
import gzip
import base64


class TestFirehoseRecordProcessor(unittest.TestCase):

    def test_transform_and_extract_from_log_event(self):
        data = [{"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}]
        data[0]["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}, {"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}]
        firehose_record_processor = FirehoseRecordProcessor(data)
        firehose_record_processor.run()
        output_records = firehose_record_processor.output_records
        self.assertEqual(len(output_records), 2)
        log_event_one = output_records[0]
        self.assertEqual(log_event_one["@log_group"], "/test/test_log_group")
        self.assertEqual(log_event_one["@log_stream"], "test_log_stream")
        self.assertEqual(log_event_one["@message"], 'with_json{"hi": "hello"}with_json')
        self.assertEqual(log_event_one["@owner"], "test_owner")
        self.assertEqual(log_event_one["@id"], 123456)
        self.assertEqual(log_event_one["hi"], '"hello"')

    def test_action_on_wrong_message_type(self):
        data = [{"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'NON_DATA_MESSAGE'}]
        data[0]["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}, {"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}]
        firehose_record_processor = FirehoseRecordProcessor(data)
        firehose_record_processor.run()
        output_records = firehose_record_processor.output_records
        self.assertEqual(len(output_records), 0)
