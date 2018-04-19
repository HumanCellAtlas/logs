from lib.es_client import ESClient
from lib import firehose_records
import unittest
import os
import time


class TestESClient(unittest.TestCase):
    test_prefix_ele = '.'.join(
        [e for e in [os.environ.get('TRAVIS_BUILD_ID'), os.environ.get('TRAVIS_EVENT_TYPE')] if e]
    )
    index_prefix = f"test{('.' + test_prefix_ele) if test_prefix_ele else ''}"""
    es_client = ESClient()
    es = es_client.es

    def test_create_cwl_day_index(self):
        try:
            index_name = self.es_client._format_today_index_name(self.index_prefix)
            if self.es.indices.exists(index_name):
                self.es_client.delete_index(index_name)
            self.assertEqual(self.es.indices.exists(index_name), False)
            self.es_client.create_cwl_day_index(self.index_prefix)
            self.assertEqual(self.es.indices.exists(index_name), True)
        finally:
            if self.es.indices.exists(index_name):
                self.es_client.delete_index(index_name)

    def test_bulk_post(self):
        try:
            index_name = self.es_client._format_today_index_name(self.index_prefix)
            if not self.es.indices.exists(index_name):
                self.es_client.create_cwl_day_index(self.index_prefix)
            self.assertEqual(self.es.indices.exists(index_name), True)
            data = [{"owner": "test_owner", "logGroup": "/test/test_log_group", "logStream": "test_log_stream", "messageType": 'DATA_MESSAGE'}]
            data[0]["logEvents"] = [{"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}, {"id": 123456, "timestamp": 1519970297000, "message": 'with_json{"hi": "hello"}with_json'}]
            record_stream = firehose_records.from_docs(data)
            output_records = list(record_stream)
            self.es_client.bulk_post(output_records, self.index_prefix)
            count = 0
            countdown = 10
            while count == 0 and countdown > 0:
                self.es.indices.refresh
                count = self.es.indices.stats(index_name)['_all']['primaries']['docs']['count']
                time.sleep(1)
                countdown -= 1
            self.assertEqual(count, 2)
        finally:
            if self.es.indices.exists(index_name):
                self.es_client.delete_index(index_name)
