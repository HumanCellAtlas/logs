import unittest
import app
import base64
import json
import gzip
from six import BytesIO

class TestApp(unittest.TestCase):

    def test_json_bounds(self):
        # Should extract bounds of json if found
        test_input = "blue{'hi': 'hello'}blueeee"
        test_output = app.json_bounds(test_input)
        self.assertEqual(test_output, (4, 18))

        # Should not return bounds if no json is found
        test_input = "blueeeeee"
        test_output = app.json_bounds(test_input)
        self.assertEqual(test_output, (None, None))

        # Should return bounds for json with internal double quote strings
        test_input = 'blue{"hi": "hello"}blueeee'
        test_output = app.json_bounds(test_input)
        self.assertEqual(test_output, (4, 18))

        # Should extract bounds even if brackets wrap invalid json
        test_input = 'blue{"hi"}blueeee'
        test_output = app.json_bounds(test_input)
        self.assertEqual(test_output, (4, 9))

        # Should extract outer bounds if there is nested json
        test_input = "blue{'hi': {'hi': hello'}}blueeee"
        test_output = app.json_bounds(test_input)
        self.assertEqual(test_output, (4, 25))

    def test_parse_json(self):
        # Should extract dict for valid json in data
        test_input = "blue{'hi': 'hello'}blueeee"
        test_output = app.parse_json(test_input)
        self.assertEqual(test_output, {"hi": "hello"})

        # Should return None if no valid json is found in data
        test_input = "blueeeeee"
        test_output = app.parse_json(test_input)
        self.assertEqual(test_output, {})

        # Should extract dict for valid json in data with internal double quote strigs
        test_input = 'blue{"hi": "hello"}blueeee'
        test_output = app.parse_json(test_input)
        self.assertEqual(test_output, {"hi": "hello"})

        # Should return None if bounded JSON is invalid
        test_input = 'blue{"hi"}blueeee'
        test_output = app.parse_json(test_input)
        self.assertEqual(test_output, {})

        # Should extract valid nested json
        test_input = "blue{'hi': {'hi': 'hello'}}blueeee"
        test_output = app.parse_json(test_input)
        self.assertEqual(test_output, {'hi': {'hi': 'hello'}})

    def test_transform_log_event(self):
        # Test transform log event with embedded json
        test_data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream"}
        test_log_event = {"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}
        test_output = app.transform_log_event(test_log_event, test_data)
        self.assertEqual(test_output["@message"], '{"hi": "hello"}')
        self.assertEqual(test_output["@id"], 123456)
        self.assertEqual(test_output["@owner"], 'test_owner')
        self.assertEqual(test_output["@log_group"], '/test/test_log_group')
        self.assertEqual(test_output["@log_stream"], 'test_log_stream')
        self.assertEqual(test_output["hi"], '"hello"')

        # Test transformed log event without embedded json
        test_data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream"}
        test_log_event = {"id": 123456, "timestamp": 1519970297000, "message": "without_json{'hi'}without_json"}
        test_output = app.transform_log_event(test_log_event, test_data)
        self.assertEqual(test_output["@message"], "without_json{'hi'}without_json")
        self.assertEqual(test_output["@id"], 123456)
        self.assertEqual(test_output["@owner"], 'test_owner')
        self.assertEqual(test_output["@log_group"], '/test/test_log_group')
        self.assertEqual(test_output["@log_stream"], 'test_log_stream')
        self.assertEqual(test_output.get("hi"), None)

    def test_parse_records_multiple_log_events(self):
        # Test for two rounds for processing for records that contain multiple log events within one record
        records_to_reingest = []
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
        data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}, {"id": 123456, "timestamp": 1519970297000, "message": "without_json{'hi'}without_json"}]
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        test_data = [{"data": base64.b64encode(out.getvalue()), "recordId": 123}]

        # Test for initial handling of multiple non-transformed log events within one record
        output = list(app.parse_records(test_data, records_to_reingest))[0]
        self.assertEqual(len(records_to_reingest), 2)
        self.assertEqual(output["result"], "Dropped")
        self.assertEqual(output["recordId"], 123)

        # Test for secondary handling of single transformed log event within one record
        for rec in records_to_reingest:
            rec['data'] = rec['Data']
            rec['recordId'] = 5000
        new_recs_to_reingest = []
        output = list(app.parse_records(records_to_reingest, new_recs_to_reingest))
        self.assertEqual(len(new_recs_to_reingest), 0)
        self.assertEqual(len(output), 2)
        output_one = output[0]
        output_two = output[1]
        output_one_data = json.loads(output_one['data'])
        output_two_data = json.loads(output_two['data'])
        self.assertEqual(output_one_data['@message'], '{"hi": "hello"}')
        self.assertEqual(output_two_data['@message'], "without_json{'hi'}without_json")

    def test_parse_records_single_log_event(self):
        # Test for two rounds for processing for records that contain single log events within one record
        records_to_reingest = []
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
        data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}]
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        test_data = [{"data": base64.b64encode(out.getvalue()), "recordId": 123}]

        # Test for initial handling of multiple non-transformed log events within one record
        output = list(app.parse_records(test_data, records_to_reingest))[0]
        self.assertEqual(len(records_to_reingest), 0)
        self.assertEqual(output['result'], 'Ok')

    def test_process_records(self):
        region = "us-east-1"
        stream_name = "Kinesis-Firehose-ELK-staging"
        data = {"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}
        data["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": "with_json{'hi': 'hello'}with_json"}, {"id": 123456, "timestamp": 1519970297000, "message": "without_json{'hi'}without_json"}]
        data = json.dumps(data).encode('utf-8')
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(data)
        input_records = [{"data": base64.b64encode(out.getvalue()), "recordId": 123}]
        list(app.process_records(input_records, region, stream_name))
