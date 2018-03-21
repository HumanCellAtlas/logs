import unittest
import json
from io import BytesIO
import gzip
import base64
from lib.firehose_record import FirehoseRecord


class TestFirehoseRecord(unittest.TestCase):

    data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
    data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}, {"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}]
    data = json.dumps(data).encode('utf-8')
    out = BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb") as f:
        f.write(data)
    firehose_record = FirehoseRecord({"data": base64.b64encode(out.getvalue()), "recordId": "12345"})
    firehose_record.decode_and_unzip()

    def test_decode_and_unzip(self):
        self.assertEqual(self.firehose_record.message_type, 'DATA_MESSAGE')
        self.assertEqual(self.firehose_record.json_data['owner'], 'test_owner')
        self.assertEqual(self.firehose_record.json_data['logGroup'], '/test/test_log_group')

    def test_transform_and_extract_from_log_event(self):
        self.firehose_record.transform_and_extract_from_log_events_in_record()
        transformed_log_events = self.firehose_record.transformed_log_events
        self.assertEqual(len(transformed_log_events), 2)
        log_event_one = transformed_log_events[0]
        self.assertEqual(log_event_one["@log_group"], "/test/test_log_group")
        self.assertEqual(log_event_one["@log_stream"], "test_log_stream")
        self.assertEqual(log_event_one["@message"], "with_json{'hi': 'hello'}with_json")
        self.assertEqual(log_event_one["@owner"], "test_owner")
        self.assertEqual(log_event_one["@id"], 123456)
        self.assertEqual(log_event_one["hi"], '"hello"')
