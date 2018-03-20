#!/usr/bin/env python
import os
import sys

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../domovoilib'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import json
import unittest
from copy import deepcopy
from datetime import datetime
from dateutil.parser import parse as dt_parse

import app


class TestApp(unittest.TestCase):

    unformatted_log_entry = {
        'insertId': 'UUID4',
        'labels': {
            'execution_id': '1234567890'
        },
        'logName': 'helloworld.log',
        'receiveTimestamp': '2017-12-24T06:27:32.635872232Z',
        'resource': {
            'labels': {
                'function_name': 'Fn1',
                'project_id': 'cool-project',
                'region': 'us-central1'
            },
            'type': 'cloud_function'
        },
        'severity': 'DEBUG',
        'textPayload': 'Wed Apr 15 20:40:51 CEST 2015 Hello, world!',
        'timestamp': '2015-04-15T20:40:52.000000000Z'
    }

    unformatted_log_entry_string = json.dumps(unformatted_log_entry)

    log_entry = {
        'timestamp': 1429130452000,
        'message': 'Wed Apr 15 20:40:51 CEST 2015 Hello, world!'
    }

    log_entry_string = json.dumps(log_entry)

    def test_format_log_entry(self):
        self.assertEqual(
            app.format_log_entry(self.unformatted_log_entry),
            self.log_entry
        )

    def test_group_entries_into_requests(self):
        recent_timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f000Z')
        recent_unformatted_log_entry = deepcopy(self.unformatted_log_entry)
        recent_unformatted_log_entry['timestamp'] = recent_timestamp
        recent_log_entry = deepcopy(self.log_entry)
        recent_log_entry['timestamp'] = int(dt_parse(recent_timestamp).timestamp() * 1000)
        unformatted_fn2 = deepcopy(recent_unformatted_log_entry)
        unformatted_fn2['resource']['labels']['function_name'] = 'Fn2'
        result, counts = app.group_entries_into_requests(
            [recent_unformatted_log_entry, unformatted_fn2, unformatted_fn2],
        )
        expected = [
            {
                'logGroupName': '/gcp/cool-project/cloud_function/Fn1',
                'logStreamName': 'default',
                'logEvents': [recent_log_entry]
            },
            {
                'logGroupName': '/gcp/cool-project/cloud_function/Fn2',
                'logStreamName': 'default',
                'logEvents': [recent_log_entry, recent_log_entry]
            },
        ]
        self.assertEqual(expected, result)

    def test_get_log_group(self):
        self.assertEqual(
            app.get_log_group(self.unformatted_log_entry),
            '/gcp/cool-project/cloud_function/Fn1'
        )


if __name__ == '__main__':
    unittest.main()
