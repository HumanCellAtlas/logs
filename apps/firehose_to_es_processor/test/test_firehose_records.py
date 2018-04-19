import unittest
from lib import firehose_records


class TestFirehoseRecordProcessor(unittest.TestCase):

    def test_transform_and_extract_from_log_event(self):
        data = [{"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}]
        data[0]["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}, {"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}]
        output_records = list(firehose_records.from_docs(data))
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
        output_records = list(firehose_records.from_docs(data))
        self.assertEqual(len(output_records), 0)
