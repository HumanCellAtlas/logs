import unittest
from lib.firehose_record import FirehoseRecord


class TestFirehoseRecord(unittest.TestCase):

    data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream",
            "messageType": 'DATA_MESSAGE'}
    data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello", "invalid?": "yes"}with_json'},
                         {"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello", "invalid?": "yes"}with_json'}]
    firehose_record = FirehoseRecord(data)

    def test_transform_and_extract_from_log_event(self):
        transformed_log_events = list(
            self.firehose_record.transform_and_extract_from_log_events_in_record()
        )
        self.assertEqual(len(transformed_log_events), 2)
        log_event_one = transformed_log_events[0]
        self.assertEqual(log_event_one["@log_group"], "/test/test_log_group")
        self.assertEqual(log_event_one["@log_stream"], "test_log_stream")
        self.assertEqual(log_event_one["@message"], 'with_json{"hi": "hello", "invalid?": "yes"}with_json')
        self.assertEqual(log_event_one["@owner"], "test_owner")
        self.assertEqual(log_event_one["@id"], 123456)
        self.assertEqual(log_event_one["hi"], '"hello"')
        self.assertIsNone(log_event_one.get('invalid?'))
