import io
import os
import sys
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from lib.json_object_stream import JsonObjectStream


class TestJsonObjectStream(unittest.TestCase):

    def test_next(self):
        str_stream = io.StringIO("""{"a":1}{"b": "\\"}\\\\"}""")
        expected = [
            {
                'a': 1
            },
            {
                'b': '\"}\\'
            }
        ]
        json_stream = JsonObjectStream(str_stream)
        result = json_stream.next()
        self.assertDictEqual(result, expected[0])
        result = json_stream.next()
        self.assertDictEqual(result, expected[1])
        self.assertIsNone(json_stream.next())


if __name__ == '__main__':
    unittest.main()
