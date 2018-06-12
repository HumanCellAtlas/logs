import os
import time
import unittest

from contextlib import contextmanager

from lib.es_client import ESClient
from elasticsearch.client import IndicesClient
from lib import firehose_records


class TestESClient(unittest.TestCase):
    test_prefix_ele = '.'.join(
        [e for e in [os.environ.get('TRAVIS_BUILD_ID'), os.environ.get('TRAVIS_EVENT_TYPE')] if e]
    )
    index_prefix = f"test{('.' + test_prefix_ele) if test_prefix_ele else ''}"""
    es_client = ESClient()
    es = es_client.es

    @contextmanager
    def new_index(self, index_name):
        try:
            if self.es.indices.exists(index_name):
                self.es_client.delete_index(index_name)
            self.es_client.create_cwl_day_index(self.index_prefix)
            yield index_name
        finally:
            if self.es.indices.exists(index_name):
                self.es_client.delete_index(index_name)

    def test_create_cwl_day_index(self):
        index_name = self.es_client._format_today_index_name(self.index_prefix)
        self.assertEqual(self.es.indices.exists(index_name), False)
        with self.new_index(index_name) as index_name:
            self.assertEqual(self.es.indices.exists(index_name), True)

    def test_bulk_post(self):
        index_name = self.es_client._format_today_index_name(self.index_prefix)
        with self.new_index(index_name):
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

    def test_tokenize(self):
        test_case = {
            "text": "2018-06-08T00:00:00Z INFO GET /v1/bundles/7ef8966b-45ef-4e0a-a51b-44a865372050.2018-06-08T230333.785338Z?param1=1&param2=2 {\"key\": \"value\"}"
        }
        index_name = self.es_client._format_today_index_name(self.index_prefix)
        index_client = IndicesClient(TestESClient.es)
        with self.new_index(index_name):
            response = index_client.analyze(index=index_name, body=test_case)
            tokens = [t['token'] for t in response['tokens']]
        self.assertEqual(set(tokens), {
            '7ef8966b-45ef-4e0a-a51b-44a865372050',
            '2018-06-08T230333.785338Z',
            ':',
            'INFO',
            '1',
            '2',
            'v1',
            'bundles',
            'key',
            'GET',
            'param2',
            'param1',
            '2018-06-08T00:00:00Z',
            'value'
        })
        self.assertEqual(len(tokens), 14)
