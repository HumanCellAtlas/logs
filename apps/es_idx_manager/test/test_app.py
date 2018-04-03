#!/usr/bin/env python
import os
import unittest
import yaml
from app import ESException, ESCleanup
import datetime


class TestApp(unittest.TestCase):

    test_prefix_ele = '.'.join(
        [e for e in [os.environ.get('TRAVIS_BUILD_ID'), os.environ.get('TRAVIS_EVENT_TYPE')] if e]
    )
    index_prefix = f"test{('.' + test_prefix_ele) if test_prefix_ele else ''}"""

    with open(os.environ['ES_IDX_MANAGER_SETTINGS'], 'r') as config_file:
        config = yaml.load(config_file)

    for cluster_config in config:
        if cluster_config["name"] == "test configuration":
            test_config = cluster_config
        cluster_config['indices'] += [{'prefix': index_prefix}]

    es = ESCleanup(None, None, test_config)


    @classmethod
    def setUpClass(cls):
        for index in cls.es.get_indices(filter_prefix=cls.index_prefix):
            index_name = index["index"]
            if index_name.startswith(cls.index_prefix):
                cls.es.delete_index(index_name)

    def test_deletion_rule(self):
        index_format = self.test_config["index_format"]

        # Should not delete index from today
        today_index_name = "test-" + datetime.datetime.today().strftime(index_format)
        today_index = {"index": today_index_name}
        self.assertEqual(self.es.should_delete_index(today_index), False)

        # Should not delete index from 6 days ago
        days_to_subtract = int(self.test_config.get('days')) - 1
        recent_index_name = "test-" + (datetime.date.today() - datetime.timedelta(days=days_to_subtract)).strftime(index_format)
        recent_index = {"index": recent_index_name}
        self.assertEqual(self.es.should_delete_index(recent_index), False)

        # Should not delete kibana index
        kibana_index = {"index": ".kibana"}
        self.assertEqual(self.es.should_delete_index(kibana_index), False)

        # Should delete index from 7 days ago
        days_to_subtract = int(self.test_config.get('days'))
        old_index_name = "test-" + (datetime.date.today() - datetime.timedelta(days=days_to_subtract)).strftime(index_format)
        old_index = {"index": old_index_name}
        self.assertEqual(self.es.should_delete_index(old_index), True)

    def test_index_deletion_pipeline(self):
        # create 10 test indices backdating from today into the past

        index_format = self.test_config["index_format"]
        test_indices = []
        for subtract in range(0, 10):
            date_str = (datetime.date.today() - datetime.timedelta(days=subtract)).strftime(index_format)
            index_name = self.index_prefix + '-' + date_str
            test_indices.append(index_name)

        # wrap creation and management in a try/finally to allow for cleanup even if test fails
        try:
            for index_name in test_indices:
                self.es.create_index(index_name)

            # Store indices before/after management of indices and ensure 3 were deleted
            pre_managed_indices_len = len(self.es.get_indices(filter_prefix=self.index_prefix))
            self.es.manage_indices()
            post_managed_indices_len = len(self.es.get_indices(filter_prefix=self.index_prefix))
            self.assertEqual(pre_managed_indices_len - 3, post_managed_indices_len)
        finally:
            # deletion of any indices. No assumptions made on test so every potential index is attempted
            for index_name in test_indices:
                try:
                    self.es.delete_index(index_name)
                except ESException as e:
                    # Error expected when index deleted in management is reattempted here
                    continue

    def test_put_index_payload(self):
        index_name = "_template/template_1"
        payloads = '''{"template": "cwl*",
                    "mappings": {
                        "fromFirehose": {
                            "dynamic_templates": [
                                {
                                  "strings": {
                                    "match_mapping_type": "string",
                                    "mapping": {
                                      "type": "text",
                                      "fields": {
                                        "raw": {
                                          "type": "text",
                                          "analyzer": "whitespace"
                                        }
                                      }
                                    }
                                  }
                                }
                              ]
                        }
                    }}'''
        self.es.put_index_payload(index_name, payloads)


if __name__ == '__main__':
    unittest.main()
