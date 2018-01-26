#!/usr/bin/env python
import os
import sys
import unittest
from copy import deepcopy
import yaml
from app import ESException, ESCleanup
import datetime


class TestApp(unittest.TestCase):

    with open(os.environ['ES_IDX_MANAGER_SETTINGS'], 'r') as config_file:
        config = yaml.load(config_file)

    cluster_config = config[0]
    es = ESCleanup(None, None, cluster_config)

    def test_fetch_indices(self):
        indices = self.es.get_indices()
        indices_names = [index['index'] for index in indices]
        # .kibana is always an index that is never deleted
        self.assertEqual('.kibana' in indices_names, True)
        # Should only ever have 7 days of logs + kibana
        self.assertEqual(len(indices) <= 8, True)

    def test_deletion_rule(self):
        index_format = self.cluster_config["index_format"]

        # Should not delete index from today
        today_index_name = "cwl-" + datetime.datetime.today().strftime(index_format)
        today_index = {"index": today_index_name}
        self.assertEqual(self.es.should_delete_index(today_index), False)

        # Should not delete index from 6 days ago
        days_to_subtract = int(self.cluster_config.get('days')) - 1
        recent_index_name = "cwl-" + (datetime.date.today() - datetime.timedelta(days=days_to_subtract)).strftime(index_format)
        recent_index = {"index": recent_index_name}
        self.assertEqual(self.es.should_delete_index(recent_index), False)

        # Should not delete kibana index
        kibana_index = {"index": ".kibana"}
        self.assertEqual(self.es.should_delete_index(kibana_index), False)

        # Should delete index from 7 days ago
        days_to_subtract = int(self.cluster_config.get('days'))
        old_index_name = "cwl-" + (datetime.date.today() - datetime.timedelta(days=days_to_subtract)).strftime(index_format)
        old_index = {"index": old_index_name}
        self.assertEqual(self.es.should_delete_index(old_index), True)


if __name__ == '__main__':
    unittest.main()
