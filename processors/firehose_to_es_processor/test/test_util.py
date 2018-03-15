import unittest
from lib.util import *


class TestUtil(unittest.TestCase):

    def test_extract_json_bounds(self):
        # Should extract bounds of json if found
        test_input = "blue{'hi': 'hello'}blueeee"
        test_output = extract_json_bounds(test_input)
        self.assertEqual(test_output, (4, 18))

        # Should not return bounds if no json is found
        test_input = "blueeeeee"
        test_output = extract_json_bounds(test_input)
        self.assertEqual(test_output, (None, None))

        # Should return bounds for json with internal double quote strings
        test_input = 'blue{"hi": "hello"}blueeee'
        test_output = extract_json_bounds(test_input)
        self.assertEqual(test_output, (4, 18))

        # Should extract bounds even if brackets wrap invalid json
        test_input = 'blue{"hi"}blueeee'
        test_output = extract_json_bounds(test_input)
        self.assertEqual(test_output, (4, 9))

        # Should extract outer bounds if there is nested json
        test_input = "blue{'hi': {'hi': hello'}}blueeee"
        test_output = extract_json_bounds(test_input)
        self.assertEqual(test_output, (4, 25))

    def test_parse_json(self):
        # Should extract dict for valid json in data
        test_input = "blue{'hi': 'hello'}blueeee"
        test_output = extract_json(test_input)
        self.assertEqual(test_output, {"hi": "hello"})

        # Should return None if no valid json is found in data
        test_input = "blueeeeee"
        test_output = extract_json(test_input)
        self.assertEqual(test_output, {})

        # Should extract dict for valid json in data with internal double quote strigs
        test_input = 'blue{"hi": "hello"}blueeee'
        test_output = extract_json(test_input)
        self.assertEqual(test_output, {"hi": "hello"})

        # Should return None if bounded JSON is invalid
        test_input = 'blue{"hi"}blueeee'
        test_output = extract_json(test_input)
        self.assertEqual(test_output, {})

        # Should extract valid nested json
        test_input = "blue{'hi': {'hi': 'hello'}}blueeee"
        test_output = extract_json(test_input)
        self.assertEqual(test_output, {'hi': {'hi': 'hello'}})

        # Should extract if message is only json
        test_input = "{'test': {'hi': 'hello'}}"
        test_output = extract_json(test_input)
        self.assertEqual(test_output, {'test': {'hi': 'hello'}})
